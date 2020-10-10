import tempfile
import os

tempdb_path = os.path.dirname(os.path.realpath(__file__))

tempdb = tempfile.mkdtemp(suffix=".sqlite3", dir=tempdb_path)
print(tempdb)
DATABASE_URI = f"sqlite:////{tempdb}"

SQLALCHEMY_DATABASE_URI = DATABASE_URI
SQLALCHEMY_TRACK_MODIFICATIONS = False

