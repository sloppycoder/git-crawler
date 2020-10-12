from flask import current_app
from datetime import datetime, timedelta
from pydriller import RepositoryMining
from gitlab.v4.objects import GroupProject
from .models import db, Author, Repository, GitCommit, RepoStatus
import re

# files matches any of the regex will not be counted
# towards commit stats
IGNORE_PATTERNS = [
    re.compile("^vendor/"),
    re.compile(".*\\.jar$"),
]


def author_count() -> int:
    return Author.query.count()


def commit_count(repo: Repository) -> int:
    return GitCommit.query.filter_by(repo=repo).count()


def first_repo(is_remote: bool) -> Repository:
    return Repository.query.filter_by(is_remote=is_remote).first()


def all_hash_for_repo(repo: Repository) -> dict:
    return dict(
        [(c.sha, c.author.id) for c in GitCommit.query.filter_by(repo=repo).all()]
    )


def should_ignore_path(path: str) -> bool:
    """
    return true if the path should be ignore
    for calculating commit stats
    """
    for regex in IGNORE_PATTERNS:
        if regex.match(path):
            return True
    return False


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


def index_repository(repo: Repository) -> int:
    if repo is None:
        return 0

    count = 0
    old_commits = all_hash_for_repo(repo)

    repo_url = repo.ssh_url if repo.is_remote else repo.name
    for commit in RepositoryMining(repo_url).traverse_commits():
        if commit.hash in old_commits:
            continue
        dev = commit.committer
        author = locate_author(name=dev.name, email=dev.email)
        git_commit = GitCommit(
            sha=commit.hash,
            message=commit.msg,
            author=author,
            repo=repo,
            created_at=commit.committer_date,
        )
        update_commit_stats(git_commit, commit.modifications)
        db.session.add(git_commit)
        count += 1
        if count % 100 == 0:
            db.session.commit()
    if count > 0:
        db.session.commit()
    return count


def update_commit_stats(git_commit: GitCommit, modifications: list) -> GitCommit:
    # TODO: evaluate how to update the stats carefully
    added, removed, nloc = 0, 0, 0
    for mod in modifications:
        if mod.change_type is None:
            continue
        file_path = mod.old_path or mod.new_path
        if should_ignore_path(file_path):
            continue
        added += mod.added
        removed += mod.removed
        nloc += mod.nloc if mod.nloc is not None else 0
    git_commit.lines_added = added
    git_commit.lines_removed = removed
    git_commit.lines_of_code = nloc
    git_commit.is_merge = added == 0 and removed == 0
    return git_commit


def index_all_repositories() -> None:
    cut_off = datetime.now() - timedelta(minutes=15)
    for repo in Repository.query.filter(
        Repository.status == RepoStatus.Ready,
        Repository.last_status_at < cut_off,
    ):
        repo_name = repo.name
        print(f"indexing repo {repo_name} ")
        try:
            n = index_repository(repo)
            print(f"indexed repo {repo_name} adding {n} new commits")
        except Exception as e:
            current_app.logger.warn(f"error when indexing repo {repo_name} => {e}")
            db.session.rollback()
            repo.last_error = str(e)

        repo.last_status_at = datetime.now()
        db.session.add(repo)
        db.session.commit()
