import io
import os.path
import gitlab
from configparser import ConfigParser
from flask import current_app

from .models import db, ConfigEntry

CONFIG_NAME = "crawler.ini"


class CrawlerConfig:
    conf: ConfigParser = None
    name: str = None
    ini: str = None

    def __init__(self, name: str = None, ini_file: str = None):
        if name is None and ini_file is None:
            raise Exception("either name or ini_file should be specified")

        if ini_file is not None:
            with open(ini_file) as f:
                self.name = name or os.path.basename(ini_file)
                self.ini = "".join(f.readlines())

        if name is not None:
            entry = ConfigEntry.query.filter_by(name=name).first()
            if entry is not None:
                self.name = name
                self.ini = entry.ini

        self.conf = ConfigParser()
        self.conf.read_file(io.StringIO(self.ini))

    def save(self) -> None:
        entry = ConfigEntry.query.filter_by(name=self.name).first()
        entry = entry or ConfigEntry(name=self.name, ini=self.ini)
        db.session.add(entry)
        db.session.commit()


def gitlab_api():
    token = current_app.config["GITLAB_TOKEN"]
    url = current_app.config["GITLAB_URL"]
    gl = gitlab.Gitlab(url, private_token=token)
    return gl


def crawler_config():
    entry = CrawlerConfig(name=CONFIG_NAME)
    return entry if entry.ini is not None else None
