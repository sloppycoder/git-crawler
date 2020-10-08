from . import app, celery
from .models import *
from celery.schedules import crontab


@celery.task()
def get_author_count():
    num_of_authors = len(Author.query.all())
    app.logger.debug(f"{num_of_authors} authors recorded")
    return num_of_authors


@celery.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(10.0, get_author_count.s())

    # sender.add_periodic_task(
    #     crontab(hour=7, minute=30, day_of_week=1),
    #     get_author_count.s()
    # )

