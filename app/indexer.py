from flask import current_app
from pydriller import RepositoryMining
from gitlab.v4.objects import GroupProject
from .models import db, Author, Repository, GitCommit, RepoStatus


def author_count() -> int:
    return Author.query.count()


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
            id=commit.hash,
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


def all_hash_for_repo(repo: Repository) -> dict:
    return dict(
        [(c.id, c.author.id) for c in GitCommit.query.filter_by(repo=repo).all()]
    )


def update_commit_stats(git_commit: GitCommit, modifications: list) -> GitCommit:
    # TODO: evaluate how to update the stats carefully
    added, removed, nloc = 0, 0, 0
    for mod in modifications:
        if mod.change_type is not None:
            # print(
            #     f"type={mod.change_type.name}, added={mod.added}, removed={mod.removed}, nloc={mod.nloc}"
            # )
            added += mod.added
            removed += mod.removed
            nloc += mod.nloc if mod.nloc is not None else 0
    git_commit.lines_added = added
    git_commit.lines_removed = removed
    git_commit.lines_of_code = nloc
    return git_commit


def commit_count(repo: Repository) -> int:
    return GitCommit.query.filter_by(repo=repo).count()


def first_repo(is_remote: bool) -> Repository:
    return Repository.query.filter_by(is_remote=is_remote).first()


def index_all_repositories() -> None:
    repo = Repository.query.filter_by(status=RepoStatus.Ready).first()
