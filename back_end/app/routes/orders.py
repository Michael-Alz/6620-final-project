import random
from typing import Any, Dict, Optional

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from ..cache import (
    ORDERS_DETAIL_KEY,
    cache_get,
    cache_setex,
    get_list_version,
    invalidate_orders_cache,
)
from ..extensions import db
from ..models import Order, OrderItem

bp = Blueprint("orders", __name__)

_SEED_CUSTOMER_NAMES = [
    "Alice Johnson",
    "Ben Carter",
    "Chloe Ramirez",
    "Darius Lee",
    "Emma Patel",
    "Felix Wright",
    "Grace Kim",
    "Hector Gomez",
    "Isla Chen",
    "Javier Torres",
]

_SEED_ITEM_NAMES = [
    "Wireless Mouse",
    "Mechanical Keyboard",
    "USB-C Hub",
    "Laptop Stand",
    "Noise Cancelling Headphones",
    "Ergonomic Chair",
    "4K Monitor",
    "Portable SSD",
    "Webcam",
    "Desk Lamp",
]

_SEED_STATUSES = ["received", "processing", "shipped", "delivered", "cancelled"]


def _require_admin_auth(body: Optional[Dict[str, Any]] = None):
    """
    Validates a simple admin password shared via header or request body.
    """
    admin_password = current_app.config.get("ADMIN_PASSWORD")
    if not admin_password:
        return (
            jsonify({"error": "Admin password is not configured on the server."}),
            500,
        )

    provided_password = request.headers.get("X-Admin-Password")
    if provided_password is None and isinstance(body, dict):
        provided_password = body.get("password")

    if provided_password != admin_password:
        return jsonify({"error": "Unauthorized."}), 401

    return None


@bp.route("/orders", methods=["GET"])
def list_orders():
    """Return all orders (no pagination) to align with the reference app."""
    version = get_list_version()
    cache_key = f"orders:list:{version}"
    cached = cache_get(cache_key)
    if cached is not None:
        return jsonify(cached)

    orders_query = (
        Order.query.options(selectinload(Order.items))
        .order_by(Order.id.desc())
    )
    orders = orders_query.all()

    response = {"total_orders": len(orders), "orders": [order.to_dict() for order in orders]}
    cache_setex(cache_key, response)

    return jsonify(response)


@bp.route("/orders/<string:order_id>", methods=["GET"])
def get_order(order_id: str):
    cache_key = ORDERS_DETAIL_KEY.format(order_id=order_id)
    cached = cache_get(cache_key)
    if cached is not None:
        return jsonify(cached)

    order = (
        Order.query.options(selectinload(Order.items))
        .filter_by(id=order_id)
        .one_or_none()
    )
    if order is None:
        return jsonify({"error": f"Order with ID '{order_id}' not found."}), 404

    payload = order.to_dict()
    cache_setex(cache_key, payload)
    return jsonify(payload)


@bp.route("/orders", methods=["POST"])
def create_order():
    data = request.get_json(silent=True) or {}

    customer_name = data.get("customer_name")
    items = data.get("items")

    if not customer_name or not isinstance(items, list) or not items:
        return (
            jsonify(
                {
                    "error": (
                        "Request must include 'customer_name' and a non-empty list of 'items'."
                    )
                }
            ),
            400,
        )

    new_order = Order(customer_name=customer_name)

    try:
        _hydrate_items(new_order, items)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    db.session.add(new_order)
    db.session.commit()

    invalidate_orders_cache(new_order.id)

    return jsonify(new_order.to_dict()), 201


@bp.route("/orders/<string:order_id>/status", methods=["PATCH"])
def update_order_status(order_id: str):
    order = Order.query.filter_by(id=order_id).one_or_none()
    if order is None:
        return jsonify({"error": f"Order with ID '{order_id}' not found."}), 404

    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    if not new_status:
        return jsonify({"error": "Request must include 'status'."}), 400

    order.status = new_status
    db.session.commit()

    invalidate_orders_cache(order.id)

    return jsonify(order.to_dict())


@bp.route("/orders/<string:order_id>", methods=["DELETE"])
def delete_order(order_id: str):
    order = Order.query.filter_by(id=order_id).one_or_none()
    if order is None:
        return jsonify({"error": f"Order with ID '{order_id}' not found."}), 404

    db.session.delete(order)
    db.session.commit()

    invalidate_orders_cache(order.id)

    return jsonify({"message": f"Order '{order_id}' has been deleted."}), 200


@bp.route("/admin/reset", methods=["POST"])
def reset_database():
    """
    Removes all orders and associated items from the database.
    Requires the admin password via header or JSON body.
    """
    body = request.get_json(silent=True)
    auth_error = _require_admin_auth(body if isinstance(body, dict) else None)
    if auth_error:
        return auth_error

    try:
        OrderItem.query.delete()
        Order.query.delete()
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Failed to reset database."}), 500

    invalidate_orders_cache()
    return jsonify({"message": "All orders have been removed."}), 200


@bp.route("/admin/seed", methods=["POST"])
def seed_database():
    """
    Populates the database with a number of fake orders.
    Expects JSON body { "count": <int> } and the admin password.
    """
    body = request.get_json(silent=True)
    parsed_body = body if isinstance(body, dict) else None

    auth_error = _require_admin_auth(parsed_body)
    if auth_error:
        return auth_error

    if isinstance(body, dict):
        count_value = body.get("count")
    elif isinstance(body, int):
        count_value = body
    else:
        count_value = None

    try:
        count = int(count_value)
    except (TypeError, ValueError):
        return jsonify({"error": "Request body must include an integer 'count' value."}), 400

    if count <= 0:
        return jsonify({"error": "'count' must be greater than zero."}), 400

    try:
        for _ in range(count):
            order = Order(
                customer_name=random.choice(_SEED_CUSTOMER_NAMES),
                status=random.choice(_SEED_STATUSES),
            )
            item_total = random.randint(1, 5)
            for _ in range(item_total):
                order.items.append(
                    OrderItem(
                        item_name=random.choice(_SEED_ITEM_NAMES),
                        quantity=random.randint(1, 5),
                    )
                )
            db.session.add(order)

        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Failed to seed database."}), 500

    invalidate_orders_cache()
    return jsonify({"message": f"Seeded {count} fake orders."}), 201


def _hydrate_items(order: Order, items: Any) -> None:
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Each item must be an object with 'name' and 'quantity'.")

        name = item.get("name")
        quantity = item.get("quantity")

        if not name or quantity is None:
            raise ValueError("Each item requires 'name' and 'quantity'.")

        try:
            quantity = int(quantity)
        except (TypeError, ValueError) as exc:
            raise ValueError("Quantity must be an integer.") from exc

        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        order_item = OrderItem(item_name=name, quantity=quantity, order=order)
        db.session.add(order_item)
