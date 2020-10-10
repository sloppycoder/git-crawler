from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class ConfigEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    ini = db.Column(db.Text)

    def __repr__(self):
        return f"""
                ConfigEntry {self.name}
                {self.ini}
                """


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    alt_emails = db.Column(db.String(512))
    tag1 = db.Column(db.String(32))
    tag2 = db.Column(db.String(32))
    tag3 = db.Column(db.String(32))

    def __repr__(self):
        return f"[Author {self.name} <{self.email}>]"


class Repository(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True, unique=True)
    type = db.Column(db.String(8), nullable=False, default="MISC")
    enabled = db.Column(db.Boolean, default=True)
    is_remote = db.Column(db.Boolean, default=False)
    http_url = db.Column(db.String(256))
    ssh_url = db.Column(db.String(256))
    last_scanned_at = db.Column(db.DateTime)
    last_error = db.Column(db.String(256))

    def __repr__(self):
        return f"[GitRepo<{self.name}>]"


class Commit(db.Model):
    id = db.Column(db.String(20), primary_key=True, nullable=False)
    author_id = db.Column(
        db.Integer,
        db.ForeignKey(f"{Author.__tablename__}.id"),
        nullable=False)
    author = db.relationship("Author", backref="author", lazy=True)
    repo_id = db.Column(
        db.Integer,
        db.ForeignKey(f"{Repository.__tablename__}.id"),
        nullable=False)
    repo = db.relationship("Repository", backref="repository", lazy=True)

    def __repr__(self):
        return f"[Commit<{self.id}>]"
