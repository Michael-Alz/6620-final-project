# Orders Service Backend

Flask + SQLAlchemy API for managing customer orders with Redis-backed caching.

## Prerequisites

-   Python 3.11+
-   Redis (Docker: `docker run -d --name redis -p 6379:6379 redis:7`)

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# ensure .env exists with the variables below
```

`.env` variables (sample in `.env`):

-   `DATABASE_URL` (default `sqlite:///database.db`)
-   `DB_USER`, `DB_PASS`, `DB_HOST`, `DB_NAME` (optional; overrides `DATABASE_URL` to connect to AWS RDS/MySQL via PyMySQL)
-   `REDIS_URL` (default `redis://localhost:6379/0`)
-   `ORDERS_CACHE_TTL` cache TTL seconds (default 30)
-   `CACHE_DISABLED=true` disables Redis operations (rollback toggle)
-   `ADMIN_PASSWORD` shared secret required for `/admin/reset` and `/admin/seed`

## Run

```bash
# start Redis first so the app connects successfully
docker start redis 2>/dev/null || docker run -d --name redis -p 6379:6379 redis:7

python run.py
```

Endpoints exposed at `http://localhost:8080`.

## Quick Start on EC2 (Redis via Docker, app via `nohup`)

```bash
# 1) Copy repo to EC2 and fill back_end/.env with your RDS creds.

# 2) Start Redis in Docker (from repo root)
sudo docker compose up -d redis

# 3) Run the Flask app outside Docker
cd back_end
source .venv/bin/activate  # or python3 -m venv .venv && source .venv/bin/activate
# Option A: dev server
nohup python3 run.py > server.log 2>&1 &
# Option B: Gunicorn (recommended for load)
gunicorn --workers 3 --threads 4 --bind 0.0.0.0:8080 run:app --daemon --log-file server.log

# 4) Confirm status
sudo docker compose ps
curl http://localhost:8080/orders
tail -f server.log

# Stop services
sudo docker compose down
# Stop whichever server you started:
pkill -f "python3 run.py"                  # dev server
pkill -f "gunicorn --workers 3 --threads"  # gunicorn daemon
pkill -f gunicorn

ps aux | grep python
ps aux | grep gunicorn
sudo lsof -i :8080
```

````

Notes:

-   `REDIS_URL` should remain `redis://localhost:6379/0` so the app talks to the Docker-hosted Redis.
-   Stop Redis with `sudo docker compose down` (add `-v` if you want to drop the Redis volume).

## Admin Endpoints

-   `POST /admin/reset` — wipes all orders/items after verifying `ADMIN_PASSWORD` via `X-Admin-Password` header or a `password` field in the JSON body.
-   `POST /admin/seed` — seeds fake orders; provide `{ "count": 100 }` plus the admin password to backfill demo data quickly.

## Cache Versioning

`GET /orders` caches the full list under `orders:list:{version}`.
Writes bump `orders:list:version` and drop affected `orders:detail:{order_id}` keys.

## Utility Scripts

Seed demo data:

```bash
python scripts/seed_orders.py --count 1000
````

Clear all orders/items:

```bash
python scripts/clear_db.py
```

Reset Redis cache (flush current DB defined by `REDIS_URL`):

```bash
python scripts/reset_redis.py
```

Or via Docker (flush cache and rebuild a clean instance):

```bash
sudo docker compose down -v redis
sudo docker compose up -d redis
```

## Load Testing

Locust file: `tests/locustfile.py`.

```bash
locust -f tests/locustfile.py --host=http://localhost:8080
# optional: observe cache activity
# docker exec -it redis redis-cli INFO stats
```

Two user types simulate 90% reads, 10% writes.

## Smoke Test Flow

```bash
curl -s -X POST http://localhost:8080/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_name":"Alice","items":[{"name":"Pen","quantity":2}]}'

curl -s http://localhost:8080/orders
```

## Checking Redis Cache

Quick ways to verify the cache is functioning.

Keys created by the service:

```bash
# List/list versioned keys
docker exec -it redis redis-cli -n 0 keys 'orders:*'

# Inspect cached list + detail payloads
docker exec -it redis redis-cli -n 0 get 'orders:list:version'          # current version number
docker exec -it redis redis-cli -n 0 ttl 'orders:list:0'                # TTL for version 0 payload
docker exec -it redis redis-cli -n 0 get 'orders:list:0'                # cached list JSON
docker exec -it redis redis-cli -n 0 keys 'orders:detail:*'             # per-order detail keys
```

Hit/miss statistics:

```bash
# Reset the statistics:
sudo docker compose exec redis redis-cli CONFIG RESETSTAT

# Check hits and misses:
sudo docker compose exec redis redis-cli info stats | egrep 'keyspace_hits|keyspace_misses'

# Percentages:
sudo docker compose exec redis sh -c \
"redis-cli info stats | awk -F: '/keyspace_hits|keyspace_misses/{gsub(/\r/,\"\",\$2); a[\$1]=\$2} END{t=a[\"keyspace_hits\"]+a[\"keyspace_misses\"]; if(t==0) print 0; else printf(\"%.2f%%\\n\", a[\"keyspace_hits\"]*100/t)}'"


# Fetch the raw counters if you prefer manual inspection
sudo docker compose exec redis redis-cli info stats | egrep 'keyspace_hits|keyspace_misses|total_commands_processed'

# Trigger a few reads (first miss, subsequent hits)
for i in {1..5}; do curl -s 'http://localhost:8080/orders' >/dev/null; done
```

Live command stream (debugging):

```bash
docker exec -it redis redis-cli monitor
```
