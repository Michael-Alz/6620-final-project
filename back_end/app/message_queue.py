"""
RabbitMQ helpers shared by the Flask app and the background worker.
"""

from __future__ import annotations

import json
import os
import ssl
import threading
from typing import Any, Dict, Optional

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import BasicProperties
from dotenv import load_dotenv

load_dotenv()

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.environ.get("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.environ.get("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.environ.get("RABBITMQ_PASSWORD", "guest")
RABBITMQ_QUEUE_NAME = os.environ.get("RABBITMQ_QUEUE_NAME", "order_write_jobs")
MQ_USE_SSL = os.environ.get("MQ_USE_SSL", "False").lower() in ("1", "true", "yes")


def build_connection_parameters() -> pika.ConnectionParameters:
    """Connection settings shared by the API and the worker."""
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    ssl_options = None
    if MQ_USE_SSL:
        ssl_context = ssl.create_default_context()
        ssl_options = pika.SSLOptions(ssl_context, RABBITMQ_HOST)
    return pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials,
        heartbeat=60,
        blocked_connection_timeout=30,
        ssl_options=ssl_options,
    )


class RabbitMQPublisher:
    """Fire-and-forget publisher used by API handlers."""

    def __init__(self):
        self._connection: Optional[pika.BlockingConnection] = None
        self._channel: Optional[BlockingChannel] = None
        self._lock = threading.Lock()

    def _ensure_channel(self) -> BlockingChannel:
        if (
            self._connection
            and not self._connection.is_closed
            and self._channel
            and self._channel.is_open
        ):
            return self._channel

        self._connection = pika.BlockingConnection(build_connection_parameters())
        self._channel = self._connection.channel()
        self._channel.queue_declare(queue=RABBITMQ_QUEUE_NAME, durable=True)
        return self._channel

    def publish(self, job: Dict[str, Any]) -> None:
        """Publishes a JSON message to the queue."""
        with self._lock:
            channel = self._ensure_channel()
            channel.basic_publish(
                exchange="",
                routing_key=RABBITMQ_QUEUE_NAME,
                body=json.dumps(job),
                properties=BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE),
            )


publisher = RabbitMQPublisher()

