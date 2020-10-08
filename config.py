from pathlib import Path
import os

db_path = Path(__file__).parent.absolute()
DATABASE_URI = f"sqlite:////{db_path}/app.sqlite3"
REDIS_URI = os.getenv("REDIS_URI", "redis://127.0.0.1:6379")

SQLALCHEMY_DATABASE_URI = DATABASE_URI
SQLALCHEMY_TRACK_MODIFICATIONS = False

CELERY_BROKER_URL = REDIS_URI
CELERY_RESULT_BACKEND = REDIS_URI
