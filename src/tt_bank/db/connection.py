"""نقطه‌ی مشترک اتصال به SQL Server برای همه‌ی فازها."""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

_PROJECT_ROOT = Path(__file__).resolve().parents[3]

load_dotenv(_PROJECT_ROOT / "config" / ".env")


def _load_config() -> dict:
    with open(_PROJECT_ROOT / "config" / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_engine() -> Engine:
    cfg = _load_config()["database"]
    driver = cfg["driver"].replace(" ", "+")
    trust = "yes" if cfg.get("trust_server_certificate") else "no"

    if os.getenv("DB_AUTH_MODE", "windows") == "sql":
        user = os.environ["DB_USER"]
        password = os.environ["DB_PASSWORD"]
        url = (
            f"mssql+pyodbc://{user}:{password}@{cfg['server']}/{cfg['name']}"
            f"?driver={driver}&TrustServerCertificate={trust}"
        )
    else:
        url = (
            f"mssql+pyodbc://@{cfg['server']}/{cfg['name']}"
            f"?driver={driver}&trusted_connection=yes&TrustServerCertificate={trust}"
        )

    return create_engine(url)
