import io
import os.path
from configparser import ConfigParser
from .models import db, ConfigEntry


class CrawlerConfig:
    conf: ConfigParser = None
    name: str = None
    ini: str = None

    def __init__(self, name: str = None, ini_file: str = None):
        if name is not None:
            entry = ConfigEntry.query.filter_by(name=name).first()
            if entry is None:
                raise Exception(f"{name} not found in config table")
            self.name = name
            self.ini = entry.ini
        elif ini_file is not None:
            with open(ini_file) as f:
                self.name = name or os.path.basename(ini_file)
                self.ini = "".join(f.readlines())
        else:
            raise Exception("either name or ini_file should be specified")

        self.conf = ConfigParser()
        self.conf.read_file(io.StringIO(self.ini))

    def save(self) -> None:
        entry = ConfigEntry.query.filter_by(name=self.name).first()
        entry = entry or ConfigEntry(name=self.name, ini=self.ini)
        db.session.add(entry)
        db.session.commit()
