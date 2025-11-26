import random
import time
import uuid
from locust import HttpUser, task, between

# --- Helper Function ---


def _generate_order_data():
    """Generates a random JSON payload for creating a new order."""
    POSSIBLE_ITEMS = ["Cheeseburger", "Fries", "Coke",
                      "Chicken Sandwich", "Salad", "Milkshake"]

    items_in_order = []
    for _ in range(random.randint(1, 3)):
        items_in_order.append({
            "name": random.choice(POSSIBLE_ITEMS),
            "quantity": random.randint(1, 2)
        })

    # This JSON structure matches the /orders POST API
    return {
        "customer_name": f"LocustUser_{uuid.uuid4()}",
        "items": items_in_order
    }

# --- Virtual User Definition ---


class FastFoodUser(HttpUser):
    # Set this to the Public IP address of your EC2 instance
    host = "http://18.219.59.42:8080"

    # Simulates a user waiting 1-3 seconds between tasks
    wait_time = between(1, 3)

    def on_start(self):
        """Called when a virtual user starts swarming."""
        # A list of all order IDs this user has created
        self.placed_order_ids = []
        # A queue of order IDs that are "received" and need processing
        self.orders_to_process = []

    @task(weight=5)
    def browse_all_orders(self):
        """Task: Simulate a user browsing all orders (high-frequency)."""
        self.client.get("/orders", name="GET /orders (all)")

    @task(weight=2)
    def place_order(self):
        """Task: Simulate a user placing a new order (mid-frequency)."""
        order_data = _generate_order_data()

        with self.client.post("/orders", json=order_data, name="POST /orders", catch_response=True) as response:
            if response.ok:
                try:
                    order_id = response.json().get("order_id")
                    if order_id:
                        # Add the new order to both lists
                        self.placed_order_ids.append(order_id)
                        self.orders_to_process.append(order_id)
                except Exception:
                    response.failure("Failed to parse JSON response")
            else:
                response.failure(
                    f"Order placement failed with status {response.status_code}")

    @task(weight=3)
    def check_own_order_status(self):
        """Task: Simulate a user checking the status of an order they placed."""
        if self.placed_order_ids:
            # Pick a random order from their history to check
            order_id = random.choice(self.placed_order_ids)
            retries = 5
            for i in range(retries):
                with self.client.get(f"/orders/{order_id}", name="GET /orders/[id]", catch_response=True) as resp:
                    if resp.status_code == 200:
                        resp.success()
                        break
                    elif resp.status_code == 404:
                        if i < retries - 1:
                            resp.success()
                            time.sleep(1)
                        else:
                            resp.failure(
                                f"Order {order_id} not found after {retries} retries")
                    else:
                        resp.failure(f"Unexpected status: {resp.status_code}")

    @task(weight=1)
    def process_an_order(self):
        """
        Task: Simulate a 'worker' processing a received order (low-frequency).
        This is an improved version that uses an in-memory queue.
        """
        if self.orders_to_process:
            # Get an order ID from the "processing queue"
            order_id = self.orders_to_process.pop(0)

            payload = {"status": "completed"}

            self.client.patch(
                f"/orders/{order_id}/status",
                json=payload,
                name="PATCH /orders/[id]/status"
            )

    @task(weight=1)
    def delete_order(self):
        """Task: Simulate a user deleting an order they placed (low-frequency)."""
        if self.placed_order_ids:
            # Pop an ID to ensure we only try to delete it once
            order_id_to_delete = self.placed_order_ids.pop(0)
            # Remove from processing queue if it's still pending there
            self.orders_to_process = [
                oid for oid in self.orders_to_process if oid != order_id_to_delete
            ]
            self.client.delete(
                f"/orders/{order_id_to_delete}",
                name="DELETE /orders/[id]"
            )
