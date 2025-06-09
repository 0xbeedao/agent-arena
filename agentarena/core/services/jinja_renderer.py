from jinja2 import Environment
from jinja2 import PackageLoader
from jinja2 import TemplateNotFound
from jinja2 import select_autoescape

from agentarena.core.exceptions import InvalidTemplateException
from agentarena.util.jinja_helpers import datetimeformat_filter
from agentarena.util.jinja_helpers import find_obj_by_id
from agentarena.util.jinja_helpers import get_attr_by_id


class JinjaRenderer:

    def __init__(self, base_path: str = "agentarena.core"):
        self.env = Environment(
            loader=PackageLoader(base_path), autoescape=select_autoescape()
        )
        self.env.filters["datetimeformat"] = datetimeformat_filter
        self.env.filters["find_obj_by_id"] = find_obj_by_id
        self.env.filters["get_attr_by_id"] = get_attr_by_id

    def get_template(self, key: str):
        possibles = [key, f"{key}.md", f"{key}.md.j2"]
        try:
            return self.env.select_template(possibles)
        except TemplateNotFound as te:
            raise InvalidTemplateException(key)

    def render_template(self, key: str, data: dict) -> str:
        possibles = [key, f"{key}.j2", f"{key}.md", f"{key}.md.j2"]
        try:
            template = self.env.select_template(possibles)
        except InvalidTemplateException as te:
            raise Exception(f"Could not find template {key}")

        return template.render(data)
