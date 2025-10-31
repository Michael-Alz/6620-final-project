import random
import sqlite3
from pathlib import Path

from locust import HttpUser, between, task


ORDER_IDS: list[str] = []
DB_PATH = Path(__file__).resolve().parent.parent / "instance" / "database.db"


def load_order_ids_from_db() -> None:
    """Preload order IDs from the SQLite database before the test starts."""
    global ORDER_IDS

    if not DB_PATH.exists():
        print(f"⚠️ Database not found at {DB_PATH}; skipping preload.")
        ORDER_IDS = []
        return

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM orders;")
            ORDER_IDS = [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as exc:
        print(f"⚠️ Could not load order IDs from database: {exc}")
        ORDER_IDS = []
        return

    print(f"✅ Loaded {len(ORDER_IDS)} order IDs from database.")


# Run preload once when locustfile is imported.
load_order_ids_from_db()


class ReaderUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(9)
    def list_orders(self) -> None:
        with self.client.get(
            "/orders?limit=50&offset=0", name="GET /orders", catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Unexpected status {response.status_code}")
                return

            try:
                response.json()
            except ValueError:
                response.failure("Invalid JSON")

    @task(1)
    def order_detail(self) -> None:
        if not ORDER_IDS:
            return
        order_id = random.choice(ORDER_IDS)
        self.client.get(f"/orders/{order_id}", name="GET /orders/:id")


# class WriterUser(HttpUser):
#     wait_time = between(1, 3)

#     @task
#     def create_order(self) -> None:
#         payload = {
#             "customer_name": f"Locust-{str(uuid.uuid4())[:8]}",
#             "items": [
#                 {"name": "PerfTestItem", "quantity": random.randint(1, 5)},
#             ],
#         }
#         self.client.post("/orders", json=payload, name="POST /orders")
