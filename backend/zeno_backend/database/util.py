"""Utility functions for database operations."""
import hashlib
import json
from pathlib import Path

import pyarrow as pa
from pyarrow import DataType

from zeno_backend.classes.base import MetadataType


def resolve_metadata_type(d: DataType) -> MetadataType:
    """Get the Zeno MetadataType of a PyArrow type.

    Args:
        d (DataType): PyArrow datatype.

    Returns:
        MetadataType: MetadataType of the column.
    """
    if pa.types.is_integer(d) or pa.types.is_floating(d) or pa.types.is_decimal(d):
        return MetadataType.CONTINUOUS
    elif pa.types.is_boolean(d):
        return MetadataType.BOOLEAN
    elif pa.types.is_temporal(d):
        return MetadataType.DATETIME
    elif pa.types.is_string(d):
        return MetadataType.NOMINAL
    return MetadataType.OTHER


def hash_api_key(api_key: str) -> str:
    """Hash an API key.

    Args:
        api_key (str): API key to hash.

    Returns:
        str: hashed API key.
    """
    hasher = hashlib.sha256()

    hasher.update(api_key.encode("utf-8"))

    return hasher.hexdigest()


def match_instance_view(view: str) -> str:
    """Get the according view specification for an instance view.

    Args:
        view (str): the view of the project.

    Returns:
        str: the view specification for the project.
    """
    if view.startswith("{"):
        return view
    views = map(
        lambda x: x.stem, list(Path("zeno_backend/instance_views").glob("*.json"))
    )
    if view in views:
        return json.dumps(
            json.load(Path(f"zeno_backend/instance_views/{view}.json").open("r"))
        )
    return json.dumps({"data": "text"})
