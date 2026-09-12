import os
import requests
from datetime import timedelta
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from jose import jwt, JWTError
import clickhouse_connect

# ── Конфигурация ──────────────────────────────────────────────
KEYCLOAK_URL = os.getenv("KC_URL", "http://keycloak:8080")
REALM_NAME = os.getenv("KC_REALM", "reports-realm")
CH_HOST = os.getenv("CH_HOST", "clickhouse")
CH_PORT = int(os.getenv("CH_PORT", "8123"))
CH_USER = os.getenv("CH_USER", "default1")
CH_PASSWORD = os.getenv("CH_PASSWORD", "123")
CH_DB = os.getenv("CH_DB", "reports")

WELL_KNOWN_CONFIG_URL = f"{KEYCLOAK_URL}/realms/{REALM_NAME}/.well-known/openid-configuration"

app = FastAPI(title="Report Service", version="2.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Подключение к ClickHouse ─────────────────────────────────
def get_ch_client():
    return clickhouse_connect.get_client(
        host=CH_HOST,
        port=CH_PORT,
        username=CH_USER,
        password=CH_PASSWORD,
        database=CH_DB,
    )

# ── Pydantic-модели ──────────────────────────────────────────
class EventRow(BaseModel):
    event_type: str
    event_count: int
    total_value: float
    first_event_date: Optional[str]
    last_event_date: Optional[str]

class ReportResponse(BaseModel):
    client_id: int
    client_name: str
    client_email: str
    events: List[EventRow]

# ── Логика валидации токена ──────────────────────────────────
def get_public_keys():
    """Загружает набор ключей (JWKS) из Keycloak."""
    try:
        resp = requests.get(WELL_KNOWN_CONFIG_URL, timeout=5)
        resp.raise_for_status()
        config = resp.json()
        jwks_url = config.get("jwks_uri")
        
        jwks_resp = requests.get(jwks_url, timeout=5)
        jwks_resp.raise_for_status()
        return jwks_resp.json()
    except Exception as e:
        # Критическая ошибка: без ключей мы не можем проверять токены
        raise HTTPException(status_code=500, detail=f"Failed to fetch Keycloak keys: {str(e)}")

# Получаем ключи при старте сервиса (один раз)
JWKS = get_public_keys()
ALGORITHM = "RS256"

def verify_token(token: str) -> Dict[str, Any]:
    """Проверяет подпись токена и его валидность."""
    try:
        payload = jwt.decode(
            token,
            JWKS,
            algorithms=[ALGORITHM],
            options={"verify_aud": False} # Отключаем проверку audience для простоты, можно включить
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

# Схема безопасности (просто парсит заголовок Authorization)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    1. Валидирует токен.
    2. Извлекает email.
    3. Находит client_id в БД по email.
    4. Возвращает данные пользователя для контекста.
    """
    payload = verify_token(token)
    
    # Пробуем взять email из стандартного поля, если нет - берем username
    email = payload.get("email") or payload.get("preferred_username")
    
    if not email:
        raise HTTPException(status_code=400, detail="Email not found in token")
    
    ch = get_ch_client()
    
    # Ищем соответствие email -> client_id
    result = ch.query(
        """
        SELECT client_id, client_name, email 
        FROM users_auth 
        WHERE email = {email:String}
        LIMIT 1
        """,
        parameters={"email": email},
    )
    
    if not result.result_rows:
        raise HTTPException(
            status_code=403, 
            detail=f"No report access configured for user: {email}. Check if email exists in ClickHouse."
        )
    
    row = result.result_rows[0]
    return {
        "client_id": row[0],
        "client_name": row[1],
        "client_email": row[2]
    }

# ── ЕДИНСТВЕННЫЙ Эндпоинт /reports ──────────────────────────
@app.get("/reports", response_model=ReportResponse)
def get_report(user: dict = Depends(get_current_user)):
    """
    Возвращает отчет только для авторизованного пользователя.
    Доступ контролируется через email в токене и маппинг в ClickHouse.
    """
    client_id = user["client_id"]
    client_name = user["client_name"]
    client_email = user["client_email"]

    ch = get_ch_client()

    rows = ch.query(
        """
        SELECT
            event_type,
            event_count,
            total_value,
            '' AS first_event_date,
            '' AS last_event_date
        FROM client_telemetry_report
        WHERE client_id = {cid:UInt32}
        ORDER BY event_type
        """,
        parameters={"cid": client_id},
    )

    events = [
        EventRow(
            event_type=r[0],
            event_count=r[1],
            total_value=float(r[2]),
            first_event_date=r[3],
            last_event_date=r[4],
        )
        for r in rows.result_rows
    ]

    return ReportResponse(
        client_id=client_id,
        client_name=client_name,
        client_email=client_email,
        events=events,
    )

@app.get("/health")
def health():
    return {"status": "ok", "service": "report_service"}
