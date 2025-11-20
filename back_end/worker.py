"""
Simple RabbitMQ worker for the Order Management System.

All writes hit the queue first so bursts of HTTP traffic do not overload
MySQL—the worker drains jobs at the database's pace, giving us back-pressure
handling. Switching from local RabbitMQ to AWS MQ just means changing the
RABBITMQ_* environment variables defined in `.env`.
"""

import json
import logging
import signal
from typing import Any, Dict

import pika
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()

from message_queue import (
    RABBITMQ_QUEUE_NAME,
    build_connection_parameters,
)
from app import app, db, Order, OrderItem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("queue-worker")


def _process_create(payload: Dict[str, Any]) -> None:
    order_id = payload["order_id"]
    with app.app_context():
        existing = Order.query.get(order_id)
        if existing:
            logger.info("Order %s already exists, skipping create.", order_id)
            return

        order = Order(
            id=order_id,
            customer_name=payload["customer_name"],
            status=payload.get("status", "received"),
        )

        for item in payload.get("items", []):
            order.items.append(
                OrderItem(
                    item_name=item["name"],
                    quantity=item["quantity"],
                )
            )

        db.session.add(order)
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            raise
        logger.info("Created order %s.", order_id)


def _process_update_status(payload: Dict[str, Any]) -> None:
    order_id = payload["order_id"]
    with app.app_context():
        order = Order.query.get(order_id)
        if not order:
            logger.warning(
                "Skipping status update because order %s does not exist.",
                order_id,
            )
            return
        order.status = payload["status"]
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            raise
        logger.info("Updated status for %s.", order_id)


def _process_delete(payload: Dict[str, Any]) -> None:
    order_id = payload["order_id"]
    with app.app_context():
        order = Order.query.get(order_id)
        if not order:
            logger.info("Order %s already gone, nothing to delete.", order_id)
            return
        db.session.delete(order)
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            raise
        logger.info("Deleted order %s.", order_id)


PROCESSORS = {
    "create_order": _process_create,
    "update_order_status": _process_update_status,
    "delete_order": _process_delete,
}


def _handle_message(channel, method, properties, body: bytes) -> None:
    try:
        job = json.loads(body)
        job_type = job["type"]
        payload = job["payload"]
        processor = PROCESSORS.get(job_type)
        if not processor:
            logger.error("Unknown job type %s. Dropping message.", job_type)
        else:
            processor(payload)
    except Exception:
        logger.exception("Failed to process job payload: %s", body)
    finally:
        channel.basic_ack(delivery_tag=method.delivery_tag)


def run_worker() -> None:
    params = build_connection_parameters()
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(
        queue=RABBITMQ_QUEUE_NAME, on_message_callback=_handle_message
    )
    logger.info("Worker listening on queue '%s'.", RABBITMQ_QUEUE_NAME)
    channel.start_consuming()


def _graceful_shutdown(signum, frame):
    logger.info("Received signal %s, exiting worker.", signum)
    raise SystemExit(0)


signal.signal(signal.SIGTERM, _graceful_shutdown)
signal.signal(signal.SIGINT, _graceful_shutdown)


if __name__ == "__main__":
    run_worker()
