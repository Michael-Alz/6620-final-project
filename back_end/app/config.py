from __future__ import annotations

import os


def _build_rds_uri() -> str | None:
    """Return an RDS URI when all DB_* env vars are set."""
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")

    if all([db_user, db_pass, db_host, db_name]):
        return f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}"
    return None


class Config:
    SQLALCHEMY_DATABASE_URI = _build_rds_uri() or os.getenv("DATABASE_URL", "sqlite:///database.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    ORDERS_CACHE_TTL = int(os.getenv("ORDERS_CACHE_TTL", "30"))
    TEMP_ORDER_CACHE_TTL = int(os.getenv("TEMP_ORDER_CACHE_TTL", "60"))
    CACHE_DISABLED = os.getenv("CACHE_DISABLED", "false").lower() == "true"
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
