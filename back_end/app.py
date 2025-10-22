"""
Order Management System Backend

This Flask application provides a RESTful API for managing customer orders.
It supports creating new orders, retrieving existing orders, and updating
order statuses.

The data model uses a normalized schema with two main tables:
- `orders`: Stores high-level information about each order (customer, status).
- `order_items`: Stores the individual items that belong to each order.
"""

import uuid
import os
from typing import Dict, Any

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

app = Flask(__name__)
CORS(app, origins="*")

# --- Database Configuration for AWS RDS ---
db_user = os.environ.get("DB_USER")
db_pass = os.environ.get("DB_PASS")
db_host = os.environ.get("DB_HOST")
db_name = os.environ.get("DB_NAME")

# DB test in local
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

# app.config["SQLALCHEMY_DATABASE_URI"] = (
#     f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}"
# )
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# --- Database Models ---
class Order(db.Model):
    """
    Represents a single customer order.

    An order has a unique ID, a customer name, a status, and contains
    one or more order items.
    """

    __tablename__ = "orders"
    id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    customer_name = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="received")
    # 'items' property will provide a list of OrderItem objects for this order
    items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the Order object to a dictionary."""
        return {
            "order_id": self.id,
            "customer_name": self.customer_name,
            "status": self.status,
            "items": [item.to_dict() for item in self.items],
        }


class OrderItem(db.Model):
    """
    Represents one item within an order.

    Each item has a name, a quantity, and a reference back to its parent Order.
    """

    __tablename__ = "order_items"
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(80), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    order_id = db.Column(
        db.String(36), db.ForeignKey("orders.id"), nullable=False
    )
    order = relationship("Order", back_populates="items")

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the OrderItem object to a dictionary."""
        return {"name": self.item_name, "quantity": self.quantity}


# --- API Endpoints ---


@app.route("/orders", methods=["POST"])
def create_order():
    """
    Creates a new order from a JSON payload.

    The payload must contain a 'customer_name' and a list of 'items',
    where each item has a 'name' and 'quantity'.

    Returns:
        JSON: The newly created order object.
        HTTP Status Code: 201 on success.
    """
    data = request.get_json()
    if not data or "customer_name" not in data or "items" not in data:
        return (
            jsonify(
                {
                    "error": "Missing `customer_name` or `items` in body."
                }
            ),
            400,
        )

    new_order = Order(customer_name=data["customer_name"])

    try:
        for item_data in data["items"]:
            if "name" not in item_data or "quantity" not in item_data:
                raise ValueError(
                    "Each item must have a 'name' and 'quantity'."
                )

            item = OrderItem(
                item_name=item_data["name"],
                quantity=item_data["quantity"],
                order=new_order,  # Associate item with the new order
            )
            db.session.add(item)
    except (ValueError, KeyError) as e:
        return jsonify({"error": str(e)}), 400

    db.session.add(new_order)
    db.session.commit()

    return jsonify(new_order.to_dict()), 201


@app.route("/orders/<string:order_id>", methods=["GET"])
def get_order(order_id: str):
    """
    Retrieves a single order by its UUID.

    Args:
        order_id (str): The unique identifier for the order.

    Returns:
        JSON: The requested order object if found.
        HTTP Status Code: 200 on success, 404 if not found.
    """
    order = Order.query.get(order_id)
    if not order:
        return (
            jsonify({"error": f"Order with ID '{order_id}' not found."}),
            404,
        )
    return jsonify(order.to_dict())


@app.route("/orders", methods=["GET"])
def get_all_orders():
    """
    Retrieves a list of all orders.

    This endpoint is more efficient as it queries the 'orders' table
    directly, rather than grouping items in the application layer.

    Returns:
        JSON: An object containing the total count and a list of orders.
        HTTP Status Code: 200.
    """
    all_orders = Order.query.all()
    return jsonify(
        {
            "total_orders": len(all_orders),
            "orders": [order.to_dict() for order in all_orders],
        }
    )


@app.route("/orders/<string:order_id>/status", methods=["PATCH"])
def update_order_status(order_id: str):
    """
    Updates the status of a specific order.

    The request body should contain a 'status' field with the new value.
    Example: { "status": "completed" }

    Args:
        order_id (str): The unique identifier for the order to update.

    Returns:
        JSON: The updated order object.
        HTTP Status Code: 200 on success, 404 if not found, 400 for bad request
    """
    order = Order.query.get(order_id)
    if not order:
        return (
            jsonify({"error": f"Order with ID '{order_id}' not found."}),
            404,
        )

    data = request.get_json()
    if not data or "status" not in data:
        return jsonify({"error": "Missing 'status' in request body."}), 400

    order.status = data["status"]
    db.session.commit()

    return jsonify(order.to_dict())


@app.route("/orders/<string:order_id>", methods=["DELETE"])
def delete_order(order_id: str):
    """
    Deletes an order by its UUID, along with all associated items.

    Args:
        order_id (str): The unique identifier for the order.

    Returns:
        JSON: A message confirming deletion or an error if not found.
        HTTP Status Code: 200 on success, 404 if not found.
    """
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": f"Order with ID '{order_id}' not found."}), 404

    db.session.delete(order)
    db.session.commit()

    return jsonify({"message": f"Order '{order_id}' has been deleted."}), 200


# --- Main Execution ---
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=8080, debug=True)
