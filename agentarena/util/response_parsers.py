import json
import uuid

from llm.utils import extract_fenced_code_block

BAD_PAYLOAD_DIR = "etc/payloads"


def write_bad_payload(payload: str):
    """
    Write a bad payload to the bad payload directory.
    """
    fname = f"{BAD_PAYLOAD_DIR}/{uuid.uuid4()}.json"
    with open(fname, "w") as f:
        f.write(payload)
    return fname


def extract_text_response(job_data: str):
    """
    Extract the text response from a Message's data.
    """
    try:
        rv = json.loads(job_data)
        if "data" in rv and isinstance(rv["data"], str):
            try:
                rv = json.loads(rv["data"])
            except json.JSONDecodeError:
                pass
        if "data" in rv:
            rv = rv["data"]
        return rv
    except json.JSONDecodeError as e:
        fname = write_bad_payload(job_data)
        raise ValueError(f"Failed to parse job data, written to {fname}")


def extract_obj_from_json(raw: str):
    """
    returns the json object if possible, extracting from fence if needed
    """
    obj = raw
    work = None
    if isinstance(raw, str):
        work = raw.replace("```json", "```")
        try:
            obj = json.loads(work)
        except json.JSONDecodeError:
            obj = work

    if isinstance(obj, str):
        try:
            obj = json.loads(f'"{obj}"')
        except json.JSONDecodeError:
            obj = work

    while isinstance(obj, dict) and "data" in obj:
        data = obj.get("data", None)
        try:
            obj = json.loads(data)
        except json.JSONDecodeError:
            obj = data
            break

    if isinstance(obj, str) and "\\n" in obj:
        while "\\n" in obj:
            obj = obj.replace("\\n", "\n")
        obj = obj.replace("\\", "")
        return extract_obj_from_json(obj)

    if isinstance(obj, str):
        if obj.find("```") != -1:
            obj = extract_fenced_code_block(obj)

    if obj and isinstance(obj, str):
        try:
            obj = json.loads(obj)
        except json.JSONDecodeError:
            pass

    if isinstance(obj, dict):
        return obj

    if obj is None:
        fname = write_bad_payload(raw)
        raise ValueError(f"Failed to parse object, written to {fname}")

    return None


def parse_list(raw, log=None):
    """
    Parse a list from a possibly nested or string-encoded structure.
    Handles cases where the features are nested under 'data', are JSON strings, or are fenced code blocks.
    """
    work = raw
    while True:
        # Unwrap 'data' if present
        if isinstance(work, dict) and "data" in work:
            work = work["data"]
            continue
        # If it's a string, try to parse it
        if isinstance(work, str):
            s = work.strip().replace("[...]", "")
            if not s:
                return []
            if not s.startswith("["):
                # We'll look for the first occurrence of '[' and the last occurrence of ']' and try to parse that substring
                start = s.find("[")
                end = s.rfind("]")
                if start != -1 and end != -1 and end > start:
                    json_str = s[start : end + 1]
                    try:
                        work = json.loads(json_str)
                        continue
                    except Exception as e:
                        fname = write_bad_payload(s)
                        if log:
                            log.error(
                                f"Failed to parse list from substring, written to {fname}",
                                error=e,
                            )
                        raise ValueError(
                            f"Failed to parse list from substring, written to {fname}"
                        )
                        return []
                # If not found, try fenced code block
                if s.find("```") != -1:
                    work = extract_obj_from_json(s)
                    continue
                # Otherwise, try to parse as JSON
                try:
                    work = json.loads(s)
                    continue
                except json.JSONDecodeError as e:
                    fname = write_bad_payload(s)
                    if log:
                        log.error(
                            f"Failed to parse list as JSON, written to {fname}", error=e
                        )
                    raise ValueError(
                        f"Failed to parse list as JSON, written to {fname}"
                    )
                    return []
            else:
                try:
                    work = json.loads(s)
                    continue
                except json.JSONDecodeError as e:
                    fname = write_bad_payload(s)
                    if log:
                        log.error(
                            f"Failed to parse list as JSON, written to {fname}",
                            error=e,
                        )
                    raise ValueError(
                        f"Failed to parse list as JSON, written to {fname}"
                    )
                    return []
        break
    return work
