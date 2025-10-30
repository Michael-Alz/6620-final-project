import random
import uuid

from locust import HttpUser, between, task

ORDER_IDS: list[str] = []


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
                data = response.json()
            except ValueError:
                response.failure("Invalid JSON")
                return

            for order in data.get("orders", []):
                order_id = order.get("order_id")
                if order_id:
                    ORDER_IDS.append(order_id)

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
