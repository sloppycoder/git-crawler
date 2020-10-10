from flask import Flask
from celery import Celery


def create_app(config_file="../config.py"):
    app = Flask(__name__)
    app.config.from_pyfile(config_file)

    from .models import db
    db.init_app(app)
    db.create_all(app=app)  # has no effect if the database file already exists

    @app.route("/ping")
    def root():
        from .tasks import get_author_count
        return f"{get_author_count()} authors"

    app.logger.info(f"create flask app {app.import_name}")
    return app


def make_celery(app=None):
    app = app or create_app()
    celery = Celery(
        app.import_name,
        broker=app.config["CELERY_BROKER_URL"]
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


celery = make_celery()
from .tasks import setup_periodic_tasks  # import for side effect only


if __name__ == "__main__":
    create_app().run()
