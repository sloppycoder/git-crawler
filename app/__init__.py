from flask import Flask
from celery import Celery


def create_app(config_file="../config.py"):
    app = Flask(__name__)
    app.config.from_pyfile(config_file)

    from .model import db, Author

    db.init_app(app)
    db.create_all(app=app)  # has no effect if the database file already exists

    @app.route("/ping")
    def root():
        result = get_author_count.delay()
        return f"{result.wait()} authors"

    app.logger.info(f"create flask app {app.import_name}")
    return app


def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


app = create_app()
celery = make_celery(app)


@celery.task()
def get_author_count():
    from .model import Author
    return len(Author.query.all())


if __name__ == "__main__":
    create_app().run()
