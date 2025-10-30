import os


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///database.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    ORDERS_CACHE_TTL = int(os.getenv("ORDERS_CACHE_TTL", "30"))
    CACHE_DISABLED = os.getenv("CACHE_DISABLED", "false").lower() == "true"
