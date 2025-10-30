# Orders Service Backend

Flask + SQLAlchemy API for managing customer orders with Redis-backed caching.

## Prerequisites
- Python 3.11+
- Redis (Docker: `docker run -d --name redis -p 6379:6379 redis:7`)

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# ensure .env exists with the variables below
```

`.env` variables (sample in `.env`):
- `DATABASE_URL` (default `sqlite:///database.db`)
- `REDIS_URL` (default `redis://localhost:6379/0`)
- `ORDERS_CACHE_TTL` cache TTL seconds (default 30)
- `CACHE_DISABLED=true` disables Redis operations (rollback toggle)

## Run
```bash
# start Redis first so the app connects successfully
docker start redis 2>/dev/null || docker run -d --name redis -p 6379:6379 redis:7

python run.py
```
Endpoints exposed at `http://localhost:8080`.

## Cache Versioning
`GET /orders` uses versioned keys `orders:list:{version}:{limit}:{offset}`.  
Writes bump `orders:list:version` and drop affected `orders:detail:{order_id}` keys.

## Utility Scripts
Seed demo data:
```bash
python scripts/seed_orders.py --count 1000
```
Clear all orders/items:
```bash
python scripts/clear_db.py
```

Reset Redis cache (flush current DB defined by `REDIS_URL`):
```bash
python scripts/reset_redis.py
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

curl -s "http://localhost:8080/orders?limit=50&offset=0"
```

## Checking Redis Cache
Quick ways to verify the cache is functioning.

Keys created by the service:
```bash
# List/list versioned keys
docker exec -it redis redis-cli -n 0 keys 'orders:*'

# Inspect a specific key
docker exec -it redis redis-cli -n 0 ttl 'orders:list:0:50:0'
docker exec -it redis redis-cli -n 0 get 'orders:list:0:50:0'
```

Hit/miss statistics:
```bash
# Capture stats before
docker exec -it redis redis-cli info stats | egrep 'keyspace_hits|keyspace_misses|total_commands_processed'

# Call an endpoint multiple times (first miss, subsequent hits)
for i in {1..5}; do curl -s 'http://localhost:8080/orders?limit=50&offset=0' >/dev/null; done

# Capture stats after
docker exec -it redis redis-cli info stats | egrep 'keyspace_hits|keyspace_misses|total_commands_processed'
```

Live command stream (debugging):
```bash
docker exec -it redis redis-cli monitor
```
