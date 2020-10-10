import os
import pytest
from app.models import db, ConfigEntry
from app.tasks import get_author_count
from app.util import CrawlerConfig


@pytest.fixture
def client():
    os.environ["FLASK_ENV"] = "test"

    from app import app
    app.config["TESTING"] = True

    with app.test_client() as client:
        with app.app_context():
            db.init_app(app)
            db.create_all(app=app)
        yield client

    try:
        # print(f"Deleting {app.config['SQLITE3_FILE']}")
        os.unlink(app.config["SQLITE3_FILE"])
    except FileNotFoundError:
        pass


def test_author_count_is_zero(client):
    with client.application.app_context():
        assert get_author_count() == 0
        resp = client.get("/ping", buffered=True)
        assert resp.response[0] == b"0 authors"


def test_crawler_config(client):

    with client.application.app_context():
        conf = CrawlerConfig(ini_file="tests/test.ini")
        sec = conf.conf.sections()
        print(sec)
        assert len(sec) > 1

        conf.save()
        saved = ConfigEntry.query.filter_by(name=conf.name).first()
        print(saved)
        assert saved is not None

