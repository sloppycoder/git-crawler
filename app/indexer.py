from flask import current_app
from pydriller import RepositoryMining
from gitlab.v4.objects import GroupProject
from .models import db, Author, Repository, Commit, RepoStatus


def author_count() -> int:
    return len(Author.query.all())


def register_remote_repository(proj: GroupProject, repo_type: str) -> Repository:
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
        f"registered remote repo {proj.name} => {proj.ssh_url_to_repo}"
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


def locate_author(name: str, email: str, create: bool = True) -> Author:
    layer = 0
    author = Author.query.filter_by(email=email).first()
    # create new author if email does not exist
    if author is None:
        if create:
            author = Author(name=name, email=email, is_alias=False)
            db.session.add(author)
            db.session.commit()
            current_app.logger.info(f"created new Author {author}")
        return author
    # recursion to find the top level author
    while True:
        if author and not author.is_alias:
            return author
        layer += 1
        if layer > 10:
            raise Exception("too many alias levels, please simplify the data")
        author = author.parent


def index_repository(repo_url: str) -> int:
    for commit in RepositoryMining(repo_url).traverse_commits():
        # author = locate_author(commit)
        assert commit.author is not None


def index_all_repositories():
    repo = Repository.query.filter_by(status=RepoStatus.Ready).first()
