from pathlib import Path

db_path = Path(__file__).parent.absolute()
DATABASE_URI = f"sqlite:////{db_path}/app.sqlite3"

SQLALCHEMY_DATABASE_URI = DATABASE_URI
SQLALCHEMY_TRACK_MODIFICATIONS = False
