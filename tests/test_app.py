import os
import pytest
from app.models import db
from app.tasks import get_author_count
from app import create_app


@pytest.fixture
def client():
    app = create_app(config_file="../config_test.py")
    app.config["TESTING"] = True

    with app.test_client() as client:
        with app.app_context():
            db.init_app(app)
            db.create_all(app=app)
        yield client

    try:
        # this does not work because the file is not close
        # how to close the file?
        os.unlink(app.config["DATABASE_URI"])
    except FileNotFoundError:
        pass


def test_author_count_is_zero(client):
    with client.application.app_context():
        assert get_author_count() == 0
        resp = client.get("/ping")
        assert resp.response[0] == b"0 authors"


