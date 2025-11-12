# Fast Food Order API - Backend

This directory (`back_end/`) contains the Python Flask backend service for the CS6620 Final Project. It provides a RESTful API for creating, retrieving, updating, and deleting food orders, storing all data in an AWS RDS (MySQL) database.

---

## Technology Stack

* **Framework:** Flask
* **Database:** Flask-SQLAlchemy (ORM)
* **Production DB:** AWS RDS (MySQL)
* **Local DB:** SQLite (for testing)
* **Driver:** `PyMySQL`
* **CORS:** `Flask-CORS` (to allow frontend access)
* **Hosting:** AWS EC2

---

## API Endpoints

All endpoints are prefixed with the server's base URL (e.g., `http://<your-ec2-public-ipv4-address>:8080`).

| Method   | Endpoint                    | Description                                    |
| :------- | :-------------------------- | :--------------------------------------------- |
| `POST`   | `/orders`                   | Creates a new order.                           |
| `GET`    | `/orders`                   | Retrieves a list of all orders.                |
| `GET`    | `/orders/<order_id>`        | Retrieves a single order by its ID.            |
| `PATCH`  | `/orders/<order_id>/status` | Updates an order's status (e.g., "completed"). |
| `DELETE` | `/orders/<order_id>`        | Deletes an order by its ID.                    |

---

## Admin Utilities

Certain maintenance actions are restricted and require the admin password configured via the `ADMIN_PASSWORD` environment variable on the server. Provide it either in the `X-Admin-Password` request header or as a `password` field in the JSON body.

| Method | Endpoint        | Description |
| :----- | :-------------- | :---------- |
| `POST` | `/admin/reset`  | Deletes all orders and associated items. Intended for quickly clearing the database during demos or tests. |
| `POST` | `/admin/seed`   | Generates fake orders using the built-in seed data. Body must include an integer `count` (e.g., `{ "count": 50 }`) indicating how many orders to create. |

Both endpoints return `401 Unauthorized` if the password is missing or incorrect.

Example request to seed 25 orders:

```bash
curl -X POST "http://<your-ec2-public-ipv4-address>:8080/admin/seed" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Password: <your-admin-password>" \
  -d '{ "count": 25 }'
```

---

## Running on the AWS EC2 Server (Production)

Follow these steps to run the server on the pre-configured EC2 instance.

### 1. Connect to the EC2 Instance

Use your terminal to SSH into the server.

```bash
ssh -i "path/to/your-key.pem" ec2-user@<your-ec2-public-dns>
```

### 2. Check Environment Variables (Automatic)

No action is needed. All required environment variables (`DB_HOST`, `DB_USER`, `DB_PASS`, `DB_NAME`) are automatically loaded from the `~/.bash_profile` script upon login.

### 3. Run the Server

We use `nohup` to run the server in the background, so it keeps running even after you close your terminal. Logs will be saved to `server.log`.

```bash
# Navigate to the backend directory
cd ~/6620-final-project/back_end

# Start the server in the background
nohup python3 app.py > server.log 2>&1 &
```

### 4. How to Check or Stop the Server

**To check the live server logs:**

```bash
tail -f server.log
```

(Press `Ctrl+C` to stop viewing logs)

**To stop the server:**

```bash
# This command will find and stop the app.py process
pkill -f app.py
```
