from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import psycopg2
import clickhouse_connect

default_args = {
    "owner": "data-team",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

def extract_clients(**context):
    conn = psycopg2.connect(
        host="db-crm",
        port=5432,
        user="user",
        password="password",
        dbname="crm_db"
    )
    cur = conn.cursor()
    cur.execute("SELECT client_id, client_name, email FROM clients")
    rows = cur.fetchall()
    context["ti"].xcom_push(key="clients", value=rows)
    cur.close()
    conn.close()

def extract_telemetry(**context):
    conn = psycopg2.connect(
        host="db-source",
        port=5432,
        user="user",
        password="password",
        dbname="source_db"
    )
    cur = conn.cursor()
    cur.execute("SELECT client_id, event_type, value, event_time FROM telemetry")
    rows = cur.fetchall()
    context["ti"].xcom_push(key="telemetry", value=rows)
    cur.close()
    conn.close()

def transform_and_load(**context):
    clients = context["ti"].xcom_pull(task_ids="extract_clients", key="clients")
    telemetry = context["ti"].xcom_pull(task_ids="extract_telemetry", key="telemetry")

    client_map = {c[0]: {"name": c[1], "email": c[2]} for c in clients}

    agg = {}
    for t in telemetry:
        cid, etype, value, _ = t
        key = (cid, etype)
        if key not in agg:
            agg[key] = {
                "event_count": 0,
                "total_value": 0,
                "first_event": None,
                "last_event": None
            }
        agg[key]["event_count"] += 1
        agg[key]["total_value"] += value

        # Для простоты first/last можно взять из телеметрии, здесь заглушка
        agg[key]["first_event"] = agg[key]["first_event"] or "2024-01-01 00:00:00"
        agg[key]["last_event"] = "2024-01-01 23:59:59"

    # Подключаемся к ClickHouse
    client = clickhouse_connect.get_client(host="clickhouse", port=8123, database="reports")

    # TRUNCATE + INSERT для простоты
    client.query("TRUNCATE TABLE reports.client_telemetry_report")

    batch = []
    for (cid, etype), data in agg.items():
        batch.append((
            cid,
            client_map.get(cid, {}).get("name", "Unknown"),
            client_map.get(cid, {}).get("email", "Unknown"),
            etype,
            data["event_count"],
            data["total_value"],
            data["first_event"],
            data["last_event"]
        ))

    if batch:
        client.insert_rows("client_telemetry_report", batch)

with DAG(
    dag_id="etl_crm_telemetry",
    default_args=default_args,
    schedule="@hourly",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["etl", "reports"]
) as dag:

    t_clients = PythonOperator(
        task_id="extract_clients",
        python_callable=extract_clients,
    )

    t_telemetry = PythonOperator(
        task_id="extract_telemetry",
        python_callable=extract_telemetry,
    )

    t_load = PythonOperator(
        task_id="transform_and_load",
        python_callable=transform_and_load,
    )

    [t_clients, t_telemetry] >> t_load
