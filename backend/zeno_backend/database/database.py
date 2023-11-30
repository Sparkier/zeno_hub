"""Functionality to interact with the database."""
import os
from configparser import ConfigParser
from pathlib import Path
from typing import Any

from psycopg_pool import AsyncConnectionPool


def config(
    filename: str = "zeno_backend/database/database.ini",
    section: str = "postgresql",
) -> dict[str, Any]:
    """Get the configuration of the database.

    Args:
        filename (str, optional): the path to the database.ini.
            Defaults to "zeno_backend/database/database.ini".
        section (str, optional): which section in the database.ini to read.
            Defaults to "postgresql".

    Raises:
        Exception: reading the configuration failed.

    Returns:
        dict[str, Any]: the database configuration.
    """
    if Path(filename).exists():
        parser = ConfigParser()
        parser.read(filename)
        db: dict[str, Any] = {}
        if parser.has_section(section):
            params = parser.items(section)
            for param in params:
                db[param[0]] = param[1]
        else:
            raise Exception(f"Section {section} not found in the {filename} file")
        return db
    else:
        db: dict[str, Any] = {}
        db["host"] = os.environ["DB_HOST"]
        db["port"] = os.environ["DB_PORT"]
        db["dbname"] = os.environ["DB_NAME"]
        db["user"] = os.environ["DB_USER"]
        db["password"] = os.environ["DB_PASSWORD"]
        return db


db_pool = AsyncConnectionPool(" ".join([f"{k}={v}" for k, v in config().items()]))
