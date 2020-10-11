from flask import Flask
from celery import Celery
import os


def config_file():
    conf = "../config.py"
    env = os.getenv("FLASK_ENV", "development")
    if env == "test":
        conf = "../config_test.py"
    return conf


def make_celery(app=None):
    celery = Celery(app.import_name, broker=app.config["CELERY_BROKER_URL"])
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile(config_file())
    print(f"===create_app using {config_file()} ===")

    from .models import db
    from .util import CrawlerConfig, crawler_config, CONFIG_NAME

    db.init_app(app)
    db.create_all(app=app)  # has no effect if the database file already exists
    # if the configuration does not exist in database
    # load from file
    with app.app_context():
        if crawler_config() is None:
            file_path = os.path.dirname(os.path.realpath(__file__))
            CrawlerConfig(
                name=CONFIG_NAME, ini_file=f"{file_path}/{CONFIG_NAME}"
            ).save()

    @app.route("/ping")
    def ping():
        from .tasks import get_author_count

        return f"{get_author_count()} authors"

    return app


app = create_app()
celery = make_celery(app)
from .tasks import setup_periodic_tasks  # import for side effect only


if __name__ == "__main__":
    create_app().run()
