from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import clickhouse_connect

def insert_row(**context):
    client = clickhouse_connect.get_client(
        host="clickhouse",
        port=8123,
        database="reports",
        username="default1",
        password="123"
    )
    client.insert(
        "users_auth",
        [
            (1, "Test User", "test@example.com", str(datetime.now()), "admin")
        ]
    )

with DAG(
    dag_id="simple_clickhouse_insert",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["demo", "clickhouse"]
) as dag:

    task = PythonOperator(
        task_id="insert_test_row",
        python_callable=insert_row
    )
