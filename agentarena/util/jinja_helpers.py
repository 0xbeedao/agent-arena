from typing import Any
from typing import Sequence

from agentarena.actors.models import Agent


def datetimeformat_filter(value, format="%Y-%m-%d %H:%M:%S"):
    """
    Jinja filter to format a timestamp as a local datetime string.
    """
    from datetime import datetime

    if value is None or value == 0:
        return "N/A"
    try:
        return datetime.fromtimestamp(value).strftime(format)
    except Exception:
        return str(value)


def find_obj_by_id(obj_list: Sequence[Any], id: str):
    """
    Find an object in a list by its ID.
    """
    for obj in obj_list:
        if getattr(obj, "id", None) == id:
            return obj
    return None


def get_attr_by_id(obj_list: Sequence[Any], id: str, attr: str):
    """
    Get an attribute from an object in a list by its ID.
    """
    if not obj_list:
        return None
    for obj in obj_list:
        if isinstance(obj, dict) and "id" in obj and obj["id"] == id:
            return obj.get(attr, None)
        elif getattr(obj, "id", None) == id:
            return getattr(obj, attr, None)
    return None
