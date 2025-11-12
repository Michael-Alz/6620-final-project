import random
import subprocess
import sys
from pathlib import Path

from locust import HttpUser, between, task


ORDER_IDS: list[str] = []
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
# Commands to reset the database and seed data.
SCRIPT_COMMANDS = [
    ("clear_db.py", [sys.executable, str(SCRIPTS_DIR / "clear_db.py")]),
    ("reset_redis.py", [sys.executable, str(SCRIPTS_DIR / "reset_redis.py")]),
    ("seed_orders.py", [sys.executable, str(SCRIPTS_DIR / "seed_orders.py")]),
]


# Clean database and seed data before running locust.
def prepare_test_data() -> None:
    """Ensure Redis and the database are prepped before Locust starts."""
    for script_name, command in SCRIPT_COMMANDS:
        print(f"▶️ Running {script_name} ...")
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as exc:
            print(f"❌ Failed to run {script_name}: {exc}")
            raise
    print("✅ Test data ready.")


# Run preparation once when locustfile is imported.
prepare_test_data()


class ReaderUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(9)
    def list_orders(self) -> None:
        global ORDER_IDS
        with self.client.get("/orders", name="GET /orders", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Unexpected status {response.status_code}")
                return

            try:
                data = response.json()
            except ValueError:
                response.failure("Invalid JSON")
                return

            ORDER_IDS = [
                order["order_id"]
                for order in data.get("orders", [])
                if isinstance(order, dict) and "order_id" in order
            ]

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
