import argparse
import random
import uuid
from pathlib import Path
import sys

from dotenv import load_dotenv

# Ensure the backend package is importable when running this script directly
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Load environment variables (e.g., REDIS_URL, DATABASE_URL)
load_dotenv(BACKEND_ROOT / ".env")

from app import create_app
from app.extensions import db
from app.models import Order, OrderItem


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed random orders for load testing.")
    parser.add_argument("--count", type=int, default=1000, help="Number of orders to create.")
    args = parser.parse_args()

    app = create_app()
    created = 0

    with app.app_context():
        for idx in range(args.count):
            order = Order(customer_name=f"Customer-{str(uuid.uuid4())[:8]}")
            item_total = random.randint(1, 5)
            for _ in range(item_total):
                db.session.add(
                    OrderItem(
                        item_name=f"Item-{random.randint(1, 20)}",
                        quantity=random.randint(1, 10),
                        order=order,
                    )
                )
            db.session.add(order)
            created += 1

            if created % 100 == 0:
                db.session.commit()

        db.session.commit()
        print(f"Created {created} orders.")


if __name__ == "__main__":
    main()
