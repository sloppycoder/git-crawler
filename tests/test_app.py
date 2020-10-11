import os
import pytest
from app.models import db
from app.tasks import get_author_count, register_git_projects
from app.util import CrawlerConfig


@pytest.fixture
def client():

    from app import app

    app.config["TESTING"] = True

    with app.test_client() as client:
        with app.app_context():
            db.init_app(app)
            db.create_all(app=app)
        yield client

    try:
        if os.getenv("FLASK_ENV") == "test":
            app.logger.warning(f"Deleting {app.config['SQLITE3_FILE']}")
            os.unlink(app.config["SQLITE3_FILE"])
    except FileNotFoundError:
        pass


def test_conf():
    return CrawlerConfig(ini_file="tests/data/test.ini").conf


def test_author_count_is_zero(client):
    with client.application.app_context():
        assert get_author_count() == 0
        resp = client.get("/ping", buffered=True)
        assert resp.response[0] == b"0 authors"


def test_crawler_config(client):
    from app.models import ConfigEntry

    with client.application.app_context():
        assert CrawlerConfig(name="does_not_exist.ini").name is None

        ini = CrawlerConfig(ini_file="tests/data/test.ini")
        assert len(ini.conf.sections()) > 1
        assert ini.name == "test.ini"

        ini.save()
        saved = ConfigEntry.query.filter_by(name=ini.name).first()
        # print(saved)
        assert saved is not None


def test_register_git_projects(client):
    with client.application.app_context():
        conf = test_conf()
        register_git_projects(conf)
