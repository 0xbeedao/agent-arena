import pytest
import json
from agentarena.util import response_parsers

# Dummy extract_fenced_code_block for test context if needed
# from llm.utils import extract_fenced_code_block


def test_extract_text_response_basic():
    data = json.dumps({"data": json.dumps({"data": "hello world"})})
    assert response_parsers.extract_text_response(data) == "hello world"


def test_extract_text_response_no_nested_data():
    data = json.dumps({"data": json.dumps({"foo": "bar"})})
    assert response_parsers.extract_text_response(data) == {"foo": "bar"}


def test_extract_fenced_json_valid_json():
    obj = {"a": 1}
    raw = json.dumps(obj)
    assert response_parsers.extract_obj_from_json(raw) == obj


def test_extract_fenced_json_invalid_json_with_fence(monkeypatch):
    raw = """```json\n{"b":2\n```"""
    assert response_parsers.extract_obj_from_json(raw) == None


def test_extract_fenced_json_invalid_json_no_fence(monkeypatch):
    monkeypatch.setattr(response_parsers, "extract_fenced_code_block", lambda s: None)
    raw = "not a json"
    result = response_parsers.extract_obj_from_json(raw)
    assert result is None


def test_extract_fenced_json_real_example():
    raw = """
```json\\n{\"action\": \"move\", \"target\": \"5,5\", \"narration\": \"Maia charges towards the flag, eyes locked on the Spectral Standard. The crowd\\'s cheers fuel her determination as she navigates the castle courtyard.\", \"memories\": \"Remember the flag\\'s location at 5,5 and the presence of other players and features like the Beweaponed Balustrade and Treacherous Tapestry.\"}\\n```
"""
    result = response_parsers.extract_obj_from_json(raw)
    assert result == {
        "action": "move",
        "target": "5,5",
        "narration": "Maia charges towards the flag, eyes locked on the Spectral Standard. The crowd's cheers fuel her determination as she navigates the castle courtyard.",
        "memories": "Remember the flag's location at 5,5 and the presence of other players and features like the Beweaponed Balustrade and Treacherous Tapestry.",
    }


def test_parse_list_simple():
    assert response_parsers.parse_list([1, 2, 3]) == [1, 2, 3]


def test_parse_list_dict_with_data():
    assert response_parsers.parse_list({"data": [4, 5]}) == [4, 5]


def test_parse_list_json_string():
    assert response_parsers.parse_list("[6,7]") == [6, 7]


def test_parse_list_nested_json_string():
    raw = json.dumps({"data": "[8,9]"})
    assert response_parsers.parse_list(json.loads(raw)) == [8, 9]


def test_parse_list_empty_string():
    assert response_parsers.parse_list("") == []


def test_parse_list_string_with_brackets():
    s = "foo [10, 11, 12] bar"
    assert response_parsers.parse_list(s) == [10, 11, 12]


def test_parse_list_fenced_code(monkeypatch):
    monkeypatch.setattr(response_parsers, "extract_obj_from_json", lambda s: "[13,14]")
    s = "```[13,14]```"
    assert response_parsers.parse_list(s) == [13, 14]


def test_parse_list_invalid_json():
    assert response_parsers.parse_list("not a list") == []


def test_parse_list_json_decode_error(monkeypatch):
    # Simulate extract_fenced_json raising error
    monkeypatch.setattr(
        response_parsers, "extract_obj_from_json", lambda s: "not a list"
    )
    assert response_parsers.parse_list("not a list") == []
