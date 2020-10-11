import glob
from configparser import ConfigParser
from pydriller import GitRepository
from git import InvalidGitRepositoryError
from celery.schedules import crontab
from . import celery
from .models import db, Author, Repository, Commit
from .util import gitlab_api, crawler_config


@celery.task()
def get_author_count():
    num_of_authors = len(Author.query.all())
    return num_of_authors


@celery.task()
def register_git_projects(conf: ConfigParser = None) -> None:
    conf = conf or crawler_config().conf
    print(f"conf={conf}")
    gl = gitlab_api()
    for key in [s for s in conf.sections() if s.find("project.") == 0]:
        section = conf[key]
        group, local_path = section.get("group"), section.get("local_path")
        project_type, filter = section.get("type", "MISC"), section.get("filter", "*")
        if local_path is None:
            try:
                # remote project, get project info from gitlab
                for proj in gl.groups.get(group).projects.list(
                    include_subgroups=True, as_list=False
                ):
                    repo = Repository.query.filter_by(
                        name=proj.path_with_namespace
                    ).first()
                    if repo is None:
                        repo = Repository(
                            name=proj.path_with_namespace,
                            is_remote=True,
                            http_url=proj.http_url_to_repo,
                            ssh_url=proj.ssh_url_to_repo,
                            type=project_type,
                        )
                    else:
                        repo.type = project_type
                    db.session.add(repo)
                    db.session.commit()
                    print(
                        f"registered remote repo {proj.name} => {proj.http_url_to_repo}"
                    )
            except Exception as e:
                print(f"Exception => {e}")
        else:
            for path in glob.glob(f"{local_path}/{filter}"):
                try:
                    if GitRepository(path).total_commits() > 0:
                        repo = Repository.query.filter_by(name=path).first()
                        if repo is None:
                            repo = Repository(
                                name=path, is_remote=False, type=project_type
                            )
                        else:
                            repo.type = project_type
                        db.session.add(repo)
                        db.session.commit()
                        print(f"registered local repo {path}")
                except InvalidGitRepositoryError:
                    print(f"skipping invalid repository path {path}")


@celery.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(60.0, get_author_count.s())

    sender.add_periodic_task(
        crontab(hour="*", minute="*/2", day_of_week="*"), register_git_projects.s()
    )
