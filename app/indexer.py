from flask import current_app
from pydriller import RepositoryMining
from .models import db, Author, Repository, Commit


def register_remote_repository(proj: dict, repo_type: str) -> Repository:
    repo = Repository.query.filter_by(name=proj.path_with_namespace).first()
    if repo is None:
        repo = Repository(
            name=proj.path_with_namespace,
            is_remote=True,
            http_url=proj.http_url_to_repo,
            ssh_url=proj.ssh_url_to_repo,
            type=repo_type,
        )
    else:
        repo.type = repo_type

    db.session.add(repo)
    db.session.commit()
    current_app.logger.info(
        f"registered remote repo {proj.name} => {proj.http_url_to_repo}"
    )

    return repo


def register_local_repository(path: str, repo_type: str) -> Repository:
    repo = Repository.query.filter_by(name=path).first()
    if repo is None:
        repo = Repository(name=path, is_remote=False, type=repo_type)
    else:
        repo.type = repo_type

    db.session.add(repo)
    db.session.commit()
    current_app.logger.info(f"registered local repo {path}")

    return repo


def author_count() -> int:
    return len(Author.query.all())
