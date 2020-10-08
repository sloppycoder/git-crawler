from flask import Flask


def create_app(config_file="../config.py"):
    app = Flask(__name__)
    app.config.from_pyfile(config_file)

    from .model import db, Author

    db.init_app(app)
    db.create_all(app=app)  # has no effect if the database file already exists

    @app.route("/")
    def root():
        return f"{len(Author.query.all())} authors"

    return app


app = create_app()


if __name__ == "__main__":
    create_app().run()
