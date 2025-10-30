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
    app = create_app()
    with app.app_context():
        items_deleted = OrderItem.query.delete()
        orders_deleted = Order.query.delete()
        db.session.commit()
        print(f"Deleted {orders_deleted} orders and {items_deleted} items.")


if __name__ == "__main__":
    main()
