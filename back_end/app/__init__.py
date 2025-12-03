import logging
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    load_dotenv = None

if load_dotenv:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import pika
from flask import Flask
from flask_cors import CORS
from sqlalchemy import text
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import SQLAlchemyError
from .config import Config
from .extensions import db, init_redis
from .message_queue import RABBITMQ_QUEUE_NAME, build_connection_parameters
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
    if not app.config.get("CACHE_DISABLED", False):
        init_redis(app)

    app.register_blueprint(orders_bp)

    with app.app_context():
        _log_database_connectivity(app)
        _log_rabbitmq_connectivity(app)

        # Auto-create tables for local development to keep setup minimal.
        if app.config.get("ENV") != "production":
            db.create_all()

    return app


def _log_database_connectivity(app: Flask) -> None:
    """Emit a best-effort connectivity check against the configured DB."""
    uri = app.config.get("SQLALCHEMY_DATABASE_URI")
    if not uri:
        app.logger.warning("SQLALCHEMY_DATABASE_URI not configured; skipping DB check.")
        return

    try:
        safe_uri = str(make_url(uri).set(password="***"))
    except Exception:  # pragma: no cover - defensive: parsing should not fail
        safe_uri = "<hidden>"

    try:
        with db.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        app.logger.info("Database reachable (%s).", safe_uri)
    except SQLAlchemyError as exc:
        app.logger.warning("Database connection failed (%s).", exc)


def _log_rabbitmq_connectivity(app: Flask) -> None:
    """Check RabbitMQ availability once at startup and log the outcome."""
    connection = None
    try:
        params = build_connection_parameters()
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.queue_declare(queue=RABBITMQ_QUEUE_NAME, durable=True)
        app.logger.info(
            "RabbitMQ connected at %s:%s (queue '%s').",
            params.host,
            params.port,
            RABBITMQ_QUEUE_NAME,
        )
    except Exception as exc:
        app.logger.warning(
            "RabbitMQ unavailable (%s); queue publishing will fail until reachable.",
            exc,
        )
    finally:
        if connection and connection.is_open:
            try:
                connection.close()
            except Exception:
                app.logger.debug("Failed to close RabbitMQ test connection.", exc_info=True)
