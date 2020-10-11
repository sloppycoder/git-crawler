import tempfile
import os

tempdb_path = os.path.dirname(os.path.realpath(__file__))
SQLITE3_FILE = tempfile.mktemp(suffix=".sqlite3", dir=tempdb_path)
REDIS_URI = os.getenv("REDIS_URI", "redis://127.0.0.1:6379")

SQLALCHEMY_DATABASE_URI = "sqlite:///" + SQLITE3_FILE
SQLALCHEMY_TRACK_MODIFICATIONS = False

CELERY_BROKER_URL = REDIS_URI
CELERY_RESULT_BACKEND = REDIS_URI

GITLAB_TOKEN = os.getenv("GITLAB_TOKEN") or "Len4R3DBCsHFRx1S65YD"
GITLAB_URL = os.getenv("GITLAB_URL") or "https://gitlab.com"
