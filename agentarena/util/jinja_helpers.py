import datetime


def datetimeformat_filter(self, value, format="%Y-%m-%d %H:%M:%S"):
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
