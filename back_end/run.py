from pathlib import Path

from dotenv import load_dotenv

from app import create_app

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
