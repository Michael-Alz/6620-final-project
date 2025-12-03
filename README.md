# Orders Service Backend (Redis + RabbitMQ)

Flask + SQLAlchemy API with Redis caching and asynchronous writes via RabbitMQ. Reads stay fast with cache; writes are queued and applied by a background worker to avoid DB spikes while keeping read-your-own-writes consistency.

## Prerequisites
- Python 3.11+
- Redis (e.g. `docker run -d --name redis -p 6379:6379 redis:7`)
- RabbitMQ / Amazon MQ (AMQP) reachable with the credentials in `.env` (local docker-compose provided)
- MySQL/RDS (optional; defaults to SQLite)

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in DB, Redis, RabbitMQ, admin secrets
```

Key `.env` variables:
- `DATABASE_URL` or `DB_USER/DB_PASS/DB_HOST/DB_NAME`
- `REDIS_URL` (default `redis://localhost:6379/0`)
- `ORDERS_CACHE_TTL` (default 30), `TEMP_ORDER_CACHE_TTL` (default 60)
- `ADMIN_PASSWORD`
- `RABBITMQ_HOST`, `RABBITMQ_PORT`, `RABBITMQ_USER`, `RABBITMQ_PASSWORD`, `RABBITMQ_QUEUE_NAME`, `MQ_USE_SSL`

### Using AWS ElastiCache (Redis) + Amazon MQ
- Point `REDIS_URL` to your ElastiCache endpoint, e.g. `REDIS_URL=rediss://<primary-endpoint>:6379/0` (use `rediss` for TLS).
- Amazon MQ (AMQP):  
  - `RABBITMQ_HOST=<amazon-mq-broker-endpoint>`  
  - `RABBITMQ_PORT=5671` for TLS/AMQPS (use 5672 if non-TLS)  
  - `RABBITMQ_USER` / `RABBITMQ_PASSWORD` = your MQ user credentials  
  - `MQ_USE_SSL=True` when using TLS (recommended)  
  - `RABBITMQ_QUEUE_NAME=order_write_jobs` (keep default unless you renamed it)
- When pointing to cloud Redis/MQ, do **not** start the local `docker compose up redis rabbitmq`.

## Running (recommended)
From `back_end/`:
```bash
# ensure Redis and RabbitMQ are up first
docker compose up -d redis rabbitmq  # from repo root, optional helper
./start_services.sh
```
- API: gunicorn `--workers 3 --threads 4 --bind 0.0.0.0:8080` (override with `API_WORKERS`, `API_THREADS`)
- Worker count default: `WORKER_COUNT=4`
- PID/log files live next to the scripts (`server.pid`, `worker_*.pid`, `server.log`, `worker_*.log`)
- Access logs: `server-access.log` captures each request (override via `ACCESS_LOG_FILE`, `ACCESS_LOG_FORMAT`)
- Startup connectivity logs show Redis/RabbitMQ/DB reachability in `server.log` (and worker logs) when the app boots

Stop everything:
```bash
./stop_services.sh
```

Manual run (if you prefer):
```bash
# start Redis and RabbitMQ separately (e.g., docker or cloud broker)
python run.py                  # API (dev server)
python worker.py               # queue consumer
```

## Write + Read Flow (async + cache)
- `POST /orders`: validate -> write full payload to Redis `temp_order:{id}` (60s TTL) -> enqueue job to RabbitMQ -> return 202 + `order_id`. No direct DB write.
- Worker (`worker.py`): consumes queue; performs SQL INSERT/UPDATE/DELETE with simulated 0.3s lag; invalidates Redis list/detail caches and lets the temp entry expire naturally to preserve the read-your-own-writes window.
- `GET /orders/<id>`: check `temp_order:{id}` first (read-your-own-writes); else cached detail `orders:detail:{id}`; else DB.
- `PATCH /orders/<id>/status` and `DELETE /orders/<id>`: enqueue jobs; return 202.
- `GET /orders`: cache key `orders:list:{version}` with version bumped on writes.

## Admin Endpoints
- `POST /admin/reset` — wipes all orders/items (requires `ADMIN_PASSWORD`)
- `POST /admin/seed` — seeds fake orders (`{ "count": 100 }` + admin password)

## Troubleshooting
- Verify brokers: `redis-cli PING`, `rabbitmqctl list_queues` (or AWS MQ console)
- If cache is disabled: set `CACHE_DISABLED=true`
- Adjust temp cache TTL: `TEMP_ORDER_CACHE_TTL`

## Load Testing
Locust file: `tests/locustfile.py`
```bash
locust -f tests/locustfile.py --host=http://localhost:8080
```
