import os
from pathlib import Path
from pydantic import BaseSettings


# This file is at: backend/app/config.py
current_file = Path(__file__)
backend_dir = current_file.parent.parent  # backend/
project_root = backend_dir.parent
env_file_path = project_root / "develop_pycharm.env"
backend_env = backend_dir / ".env"


class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DATABASE: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    MONGODB_URL: str
    UVICORN_HOST: str
    # MongoDB: timeout (ms) for connection/selection; fallback to JSON when Mongo unreachable
    MONGODB_TIMEOUT_MS: int = 15000
    MONGODB_FALLBACK_JSON: bool = True
    # CORS origins - comma-separated list, or '*' for all (not recommended in production)
    ALLOWED_ORIGINS: str = "http://localhost:8080,http://127.0.0.1:8080,http://localhost:80,http://127.0.0.1:80"

    # Pedidos Chegando (Gmail + IA) — optional; leave empty if not using pipeline
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REFRESH_TOKEN: str = ""
    GMAIL_ADDRESS: str = ""
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    ANTHROPIC_API_KEY: str = ""
    CONFIDENCE_THRESHOLD: float = 0.75
    PEDIDOS_AUTO_CONFIRM: bool = False  # When False, new orders require manual review (needs-review)
    # Skip Gemini for emails already imported (saves API calls when re-syncing same date range)
    PEDIDOS_SKIP_ALREADY_IMPORTED: bool = True
    SYNC_INTERVAL_MINUTES: int = 15
    SUBJECT_KEYWORDS: str = "pedido,order,encomenda,compra,notificacao"
    INVOICE_KEYWORDS: str = "NF-e,nota fiscal,fatura,danfe,DANFE,remessa,embarque"
    # Exclude from Pedidos Chegando: monthly invoices, CDL, boletos, etc. (NF-e go to separate tab)
    SUBJECT_EXCLUDE_KEYWORDS: str = "fatura cdl,fatura referente,notificacao de emissao de boleto bancario,boleto bancario"
    BACKFILL_FROM_DATE: str = "2019-01-01"
    UPLOAD_DIR: str = "./uploads"

    # Cartão / Conciliação — Stone
    STONE_AFFILIATION_CODE: str = "232084871"
    STONE_BEARER_TOKEN: str = ""
    STONE_AUTH_RAW: str = ""
    STONE_AUTH_ENCRYPTED: str = ""
    # Cartão / Conciliação — Sicredi Máquinas (opcional)
    SICREDI_API_URL: str = ""
    SICREDI_API_TOKEN: str = ""
    SICREDI_ESTABELECIMENTO_ID: str = ""

    class Config:
        env_file = [str(env_file_path)] + ([str(backend_env)] if backend_env.exists() else [])
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
