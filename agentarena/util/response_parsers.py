import json

from llm.utils import extract_fenced_code_block


def extract_text_response(job_data: str):
    """
    Extract the text response from a Message's data.
    """
    rv = json.loads(job_data)
    if "data" in rv:
        rv = json.loads(rv["data"])
    if "data" in rv:
        rv = rv["data"]
    return rv


def extract_fenced_json(raw: str):
    """
    returns the json object if possible, extracting from fence if needed
    """
    try:
        obj = json.loads(raw)
        return obj
    except json.JSONDecodeError:
        pass
    work = extract_fenced_code_block(raw)
    return work or raw


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
            s = work.strip()
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
                        if log:
                            log.error("Failed to parse list from substring", error=e)
                        return []
                # If not found, try fenced code block
                if s.find("```") != -1:
                    work = extract_fenced_json(s)
                    continue
                # Otherwise, try to parse as JSON
                try:
                    work = json.loads(s)
                    continue
                except Exception as e:
                    if log:
                        log.error("Failed to parse list as JSON", error=e)
                    return []
            else:
                try:
                    work = json.loads(s)
                    continue
                except Exception as e:
                    if log:
                        log.error("Failed to parse list as JSON", error=e)
                    return []
        break
    return work
