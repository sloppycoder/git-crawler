import os
import pytest
import zipfile
from pydriller import GitRepository
from app.models import db
from app.tasks import get_author_count, register_git_projects
from app.indexer import (
    locate_author,
    author_count,
    index_repository,
    index_all_repositories,
    commit_count,
    first_repo,
)
from app.util import CrawlerConfig


@pytest.fixture
def client(tmp_path):
    from app import app

    app.config["TESTING"] = True

    with app.test_client() as client:
        with app.app_context():
            db.init_app(app)
            db.create_all(app=app)
            client.crawler_conf = prep_test_conf(tmp_path)
        yield client

    try:
        if os.getenv("FLASK_ENV") == "test" and os.getenv("KEEP_TMPDB") != "yes":
            app.logger.warning(f"Deleting {app.config['SQLITE3_FILE']}")
            os.unlink(app.config["SQLITE3_FILE"])
    except FileNotFoundError:
        pass


def prep_test_conf(tmp_path):
    # prepare test files
    with zipfile.ZipFile("tests/data/repo1.zip", "r") as zip_ref:
        zip_ref.extractall(tmp_path)
    with zipfile.ZipFile("tests/data/not_a_repo.zip", "r") as zip_ref:
        zip_ref.extractall(tmp_path)
    conf = CrawlerConfig(ini_file="tests/data/test.ini").conf
    conf["project.local"]["local_path"] = str(tmp_path)
    return conf


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


@pytest.mark.dependency()
def test_register_git_projects(client, tmp_path):
    with client.application.app_context():
        register_git_projects(client.crawler_conf)
        local_repo = first_repo(is_remote=False)
        assert local_repo is not None


def test_find_author(client):
    with client.application.app_context():
        total = author_count()

        # set create flag to False won't create any author
        dev0 = locate_author("dev1", "dev1@banana.com", create=False)
        assert dev0 is None
        assert author_count() == total

        # create first author
        dev1 = locate_author("dev1", "dev1@banana.com")
        assert dev1 is not None
        assert author_count() == total + 1

        dev2 = locate_author("dev1", "dev1@banana.org")
        assert dev2 is not None
        assert author_count() == total + 2

        # set dev1 to be dev2's parent
        dev2.is_alias = True
        dev2.parent = dev1
        db.session.add(dev2)
        db.session.commit()

        dev3 = locate_author("dev1", "dev1@banana.org")
        assert dev3.email == dev1.email

        # cleanup what we created during testing
        db.session.delete(dev1)
        db.session.delete(dev2)
        db.session.commit()
        assert author_count() == total


@pytest.mark.dependency(depends=["test_register_git_projects"])
def test_index_repository(client):
    with client.application.app_context():
        repo = first_repo(is_remote=False)
        new_commits = index_repository(repo)
        records_in_db = commit_count(repo)

        # print(f"new_commits = {new_commits}, records_in_db = {records_in_db}")
        assert records_in_db == new_commits
        assert author_count() == 2  # what's the right number?

        # create some test commits and only new commits will be indexed
        create_some_commit(repo.name, "d1.txt")
        create_some_commit(repo.name, "d2.asc")
        assert index_repository(repo) == 2


def test_index_remote_repository(client):
    with client.application.app_context():
        index_repository(first_repo(is_remote=True))


@pytest.mark.dependency(depends=["test_register_git_projects"])
def test_index_all_repositories(client):
    with client.application.app_context():
        index_all_repositories()


def create_some_commit(repo_path: str, file_name: str = "dummy.txt") -> None:
    repo = GitRepository(repo_path).repo
    a_file = f"{repo_path}/{file_name}"
    with open(a_file, "w") as f:
        f.write("something\n")
    repo.index.add(a_file)
    repo.index.commit("some commit")
