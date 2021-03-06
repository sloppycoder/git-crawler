from flask_sqlalchemy import SQLAlchemy
import datetime
import enum

db = SQLAlchemy()


class RepoStatus(enum.Enum):
    Ready = 1
    InUse = 2
    Error = 3
    Disabled = 99


class ConfigEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    ini = db.Column(db.Text)

    def __repr__(self):
        return f"""ConfigEntry {self.name}
                {self.ini}
                """


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    tag1 = db.Column(db.String(32))
    tag2 = db.Column(db.String(32))
    tag3 = db.Column(db.String(32))
    is_alias = db.Column(db.Boolean, default=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("author.id"), nullable=True)
    parent = db.relationship("Author", remote_side=[id])

    def __repr__(self):
        return f"[Author<{self.email}>]"


class Repository(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(512), index=True, unique=True)
    type = db.Column(db.String(8), nullable=False, default="MISC")
    enabled = db.Column(db.Boolean, default=True)
    is_remote = db.Column(db.Boolean, default=False)
    http_url = db.Column(db.String(256))
    ssh_url = db.Column(db.String(256))
    status = db.Column(db.Enum(RepoStatus), default=RepoStatus.Ready)
    last_status_at = db.Column(db.DateTime, default=datetime.datetime.fromtimestamp(0))
    last_error = db.Column(db.String(256))

    def __repr__(self):
        return f"[Repository<{self.name}>]"


class GitCommit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sha = db.Column(db.String(20), nullable=False)
    message = db.Column(db.String(2048))
    lines_added = db.Column(db.Integer)
    lines_removed = db.Column(db.Integer)
    lines_of_code = db.Column(db.Integer)
    is_merge = db.Column(db.Boolean, default=False)
    author_id = db.Column(
        db.Integer, db.ForeignKey(f"{Author.__tablename__}.id"), nullable=False
    )
    author = db.relationship("Author", backref="author", lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.fromtimestamp(0))
    repo_id = db.Column(
        db.Integer, db.ForeignKey(f"{Repository.__tablename__}.id"), nullable=False
    )
    repo = db.relationship("Repository", backref="repository", lazy=True)

    def __repr__(self):
        return f"[Commit<{self.id}>]"
