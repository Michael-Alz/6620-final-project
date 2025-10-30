from pathlib import Path
import sys

from dotenv import load_dotenv
import redis as redis_lib

# Ensure the backend package path is importable (symmetry with other scripts)
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Load env (so REDIS_URL is available)
load_dotenv(BACKEND_ROOT / ".env")

from app.config import Config  # noqa: E402


def main() -> None:
    url = Config.REDIS_URL
    client = redis_lib.from_url(url, decode_responses=True)

    try:
        dbsize_before = client.dbsize()
        client.flushdb()  # flush only the selected DB
        dbsize_after = client.dbsize()
    except redis_lib.RedisError as exc:  # type: ignore[attr-defined]
        print(f"Failed to reset Redis DB at {url}: {exc}")
        raise SystemExit(1)

    print(
        f"Flushed Redis database at {url}. Keys before: {dbsize_before}, after: {dbsize_after}."
    )


if __name__ == "__main__":
    main()


