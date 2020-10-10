import glob
from . import celery
from .models import *
from .util import *
from celery.schedules import crontab


@celery.task()
def get_author_count():
    num_of_authors = len(Author.query.all())
    return num_of_authors


@celery.task()
def register_git_projects(conf: ConfigParser) -> None:
    gl = gitlab_api()
    for key in [s for s in conf.sections() if s.find("project.") == 0]:
        section = conf[key]
        group, local_path = section.get("group"), section.get("local_path")
        project_type, filter = section.get("type", "MISC"), section.get("filter", "*")
        if local_path is None:
            # remote project, get project info from gitlab
            for proj in gl.groups.get(group).projects.list(include_subgroups=True, as_list=False):
                print(f"{proj.name} => {proj.http_url_to_repo}")
        else:
            for dir in glob.glob(f"{local_path}/{filter}"):
                print(dir)



@celery.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(10.0, get_author_count.s())

    # sender.add_periodic_task(
    #     crontab(hour=7, minute=30, day_of_week=1),
    #     get_author_count.s()
    # )

