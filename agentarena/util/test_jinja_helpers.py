import datetime

from pydantic import BaseModel
from pydantic import Field

from agentarena.util.jinja_helpers import datetimeformat_filter
from agentarena.util.jinja_helpers import find_obj_by_id


class DummyModel(BaseModel):
    id: str = Field("id")
    test: str = Field("test")

    def __init__(self, id):
        super().__init__()
        self.id = id
        self.test = "test"


def test_datetimeformat_filter_valid_timestamp():
    # 1609459200 = 2021-01-01 00:00:00 UTC
    now = datetime.datetime.now()

    assert datetimeformat_filter(int(now.timestamp())) == now.strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def test_datetimeformat_filter_custom_format():
    # 1609459200 = 2021-01-01 00:00:00 UTC
    assert len(datetimeformat_filter(1609459200, "%Y/%m/%d").split("/")) == 3


def test_datetimeformat_filter_none():
    assert datetimeformat_filter(None) == "N/A"


def test_datetimeformat_filter_zero():
    assert datetimeformat_filter(0) == "N/A"


def test_datetimeformat_filter_invalid():
    # Pass a string, should return the string itself
    assert datetimeformat_filter("not_a_timestamp") == "not_a_timestamp"


def test_find_obj_by_id_found():
    objs = [DummyModel("a"), DummyModel("b"), DummyModel("c")]
    result = find_obj_by_id(objs, "b")
    assert result is objs[1]


def test_find_obj_by_id_not_found():
    objs = [DummyModel("a"), DummyModel("b")]
    result = find_obj_by_id(objs, "z")
    assert result is None


def test_find_obj_by_id_empty_list():
    result = find_obj_by_id([], "a")
    assert result is None
