from typing import Any

from flask import Blueprint, jsonify, request
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


@bp.route("/orders", methods=["GET"])
def list_orders():
    try:
        limit = int(request.args.get("limit", 50))
    except (TypeError, ValueError):
        limit = 50
    limit = max(1, min(limit, 200))

    try:
        offset = int(request.args.get("offset", 0))
    except (TypeError, ValueError):
        offset = 0
    offset = max(offset, 0)

    version = get_list_version()
    cache_key = f"orders:list:{version}:{limit}:{offset}"
    cached = cache_get(cache_key)
    if cached is not None:
        return jsonify(cached)

    orders_query = (
        Order.query.options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )
    paged_orders = orders_query.offset(offset).limit(limit).all()

    response = {
        "count": len(paged_orders),
        "next_offset": offset + len(paged_orders),
        "orders": [order.to_dict() for order in paged_orders],
    }
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
