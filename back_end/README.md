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

## Running Locally with RabbitMQ

Write operations now flow through RabbitMQ for back-pressure control, so the Flask app and the queue worker both need to run. Reads (`GET /orders*`) still hit the DB synchronously.

1. **Install dependencies**

   ```bash
   cd back_end
   pip install -r requirements.txt
   cp .env.example .env   # then edit it with real DB + RabbitMQ credentials
   ```

2. **Start RabbitMQ via Docker**

   A minimal compose file is included:

   ```bash
   cd back_end
   docker compose up -d rabbitmq
   ```

   This exposes AMQP on `localhost:5672` and the management UI on `http://localhost:15672` (default user/pass `guest/guest` unless overridden in `.env`).

   **Purge the queue for a clean test run:**

   ```bash
   cd back_end
   # Make sure the rabbitmq service is running (use `docker compose ps`)
   docker compose exec rabbitmq \
     rabbitmqctl purge_queue "${RABBITMQ_QUEUE_NAME:-order_write_jobs}"
   ```

   (`rabbitmqctl` ships in the container, so no extra CLI download is needed. Clearing the queue is handy before rerunning Locust.)

3. **Run the Flask API**

   ```bash
   # in one terminal
   cd back_end
   flask --app app run --host 0.0.0.0 --port 8080
   # or python app.py if you prefer the previous entry point
   ```

4. **Run the queue worker**

   ```bash
   # in a second terminal
   cd back_end
   python worker.py
   ```

   The worker consumes the queue and performs DB writes at the pace MySQL can handle, so HTTP requests see quick `202 Accepted` responses even under load.

5. **Optional: seeded data or admin tasks**

   Use the `/admin/seed` and `/admin/reset` endpoints with the `X-Admin-Password` header just like before.

## Running on the AWS EC2 Server (Production)

For EC2 you follow the same overall flow, but you can point `RABBITMQ_HOST`, `RABBITMQ_PORT`, `RABBITMQ_USER`, and `RABBITMQ_PASSWORD` to either the local Docker broker (during testing) or an Amazon MQ broker (AMQP). The queue name stays the same unless you change `RABBITMQ_QUEUE_NAME`.

1. **Connect to the EC2 instance**

   ```bash
   ssh -i "path/to/your-key.pem" ec2-user@<your-ec2-public-dns>
   ```

2. **Export environment variables**

    - Copy `.env.example` to `~/6620-final-project/back_end/.env`.
    - Fill in the DB credentials (pointing to RDS).
    - Point the RabbitMQ variables to your Amazon MQ (or to the Docker container IP if you run RabbitMQ on the EC2 host).
    - Source the env file (`export $(grep -v '^#' .env | xargs)`), or add the exports to your shell profile.

3. **Start RabbitMQ**

    - **Using Docker on the EC2 host:** `cd ~/6620-final-project/back_end && docker compose up -d rabbitmq`
    - **Using Amazon MQ:** skip Docker; just ensure the security groups allow AMQP from the EC2 instance to the broker and the `.env` variables reference the broker endpoint.
    - To purge the queue on the EC2 host when using Docker: `cd ~/6620-final-project/back_end && docker compose exec rabbitmq rabbitmqctl purge_queue "${RABBITMQ_QUEUE_NAME:-order_write_jobs}"`. If you connect to Amazon MQ instead, use the AWS console or a `rabbitmqadmin` CLI pointed at that broker endpoint.

4. **Run the Flask API + workers (background)**

   ```bash
   cd ~/6620-final-project/back_end
   WORKER_COUNT=2 ./start_services.sh   # starts API + N workers (pid/log per worker)
   ```

5. **Check logs (follow)**

   ```bash
   tail -f server.log    # API logs
   tail -f worker_1.log  # worker logs (one per worker)
   ```

6. **Check or stop services**

   ```bash
   ./stop_services.sh    # stops API + worker using pid files
   docker compose down   # stop local RabbitMQ if running via Docker
   ```

Switching from local RabbitMQ to Amazon MQ later only requires updating the `RABBITMQ_*` environment variables—no code changes are necessary.
