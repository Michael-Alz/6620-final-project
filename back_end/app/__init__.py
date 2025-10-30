import logging
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    load_dotenv = None

if load_dotenv:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from flask import Flask
from flask_cors import CORS
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from .config import Config
from .extensions import db, init_redis
from .routes.orders import bp as orders_bp


def create_app(config_class=Config) -> Flask:
    """Application factory that wires config, extensions, and blueprints."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app, origins="*")

    # Ensure our application logger emits info-level messages by default so we
    # can observe Redis connection status without extra configuration.
    if app.logger.getEffectiveLevel() > logging.INFO:
        app.logger.setLevel(logging.INFO)
        for handler in app.logger.handlers:
            handler.setLevel(logging.INFO)

    db.init_app(app)
    init_redis(app)

    app.register_blueprint(orders_bp)

    # Auto-create tables for local development to keep setup minimal.
    if app.config.get("ENV") != "production":
        with app.app_context():
            db.create_all()
            _ensure_created_at_column()

    return app


def _ensure_created_at_column() -> None:
    """Backfill the created_at column for SQLite dev databases."""
    engine = db.engine
    if engine.url.get_backend_name() != "sqlite":
        return

    inspector = inspect(engine)
    try:
        columns = inspector.get_columns("orders")
    except SQLAlchemyError:
        return

    if any(col["name"] == "created_at" for col in columns):
        return

    with engine.begin() as connection:
        try:
            connection.execute(text("ALTER TABLE orders ADD COLUMN created_at DATETIME"))
        except SQLAlchemyError:
            return
        connection.execute(
            text("UPDATE orders SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
        )
