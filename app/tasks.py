import glob
from os.path import expanduser
from flask import current_app
from configparser import ConfigParser
from celery.schedules import crontab
from pydriller import GitRepository
from git import InvalidGitRepositoryError
from gitlab import GitlabGetError

from . import celery
from .util import gitlab_api, crawler_config
from .indexer import register_remote_repository, register_local_repository, author_count


@celery.task()
def get_author_count():
    return author_count()


@celery.task()
def register_git_projects(conf: ConfigParser = None) -> None:
    conf = conf or crawler_config().conf
    gl = gitlab_api()
    for key in [s for s in conf.sections() if s.find("project.") == 0]:
        section = conf[key]
        group, local_path = section.get("group"), section.get("local_path")
        if local_path and local_path[0] == "~":
            local_path = expanduser(local_path)
        project_type, filter = section.get("type", "MISC"), section.get("filter", "*")
        if local_path is None:
            # remote project, get project info from gitlab
            try:
                for proj in gl.groups.get(group).projects.list(
                    include_subgroups=True, as_list=False
                ):
                    register_remote_repository(proj, project_type)
            except GitlabGetError as e:
                current_app.logger.info(f"gitlab search {group} has some error {e}")
        else:
            for path in glob.glob(f"{local_path}/{filter}", recursive=True):
                try:
                    if GitRepository(path).total_commits() > 0:
                        register_local_repository(path, project_type)
                except InvalidGitRepositoryError:
                    current_app.logger.info(f"skipping non Git path {path}")
                except Exception:
                    current_app.logger.info(f"skipping invalid repository path {path}")


@celery.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(60.0, get_author_count.s())

    sender.add_periodic_task(
        crontab(hour="*", minute="*/2", day_of_week="*"), register_git_projects.s()
    )
