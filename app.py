"""Order Management System Backend"""

import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=[ 'http://localhost:5174'])  # Enable CORS for frontend ports

# --- In-Memory Database ---
# We'll use a simple Python dictionary to act as our database for now.
# The keys will be order_ids and the values will be the order data.
orders = {}


@app.route("/orders", methods=["POST"])
def create_order():
    """
    Creates a new order.
    Expects a JSON body with order details, for example:
    {
        "customer_name": "John Doe",
        "items": [
            {"name": "Cheeseburger", "quantity": 1},
            {"name": "Fries", "quantity": 1},
            {"name": "Coke", "quantity": 1}
        ]
    }
    """
    order_data = request.get_json()
    if not order_data or "items" not in order_data:
        return jsonify({"error": "Invalid order data. 'items' field is required."}), 400
    order_id = str(uuid.uuid4())
    orders[order_id] = {
        "order_id": order_id,
        "customer_name": order_data.get("customer_name", "N/A"),
        "items": order_data["items"],
        "status": "received",
    }
    return jsonify(orders[order_id]), 201


@app.route("/orders/<string:order_id>", methods=["GET"])
def get_order(order_id):
    """
    Retrieves a specific order by its ID.
    """
    order = orders.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(order)


@app.route("/orders", methods=["GET"])
def get_all_orders():
    """
    Retrieves all orders stored in memory.
    """
    return jsonify({
        "total_orders": len(orders),
        "orders": list(orders.values())
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
