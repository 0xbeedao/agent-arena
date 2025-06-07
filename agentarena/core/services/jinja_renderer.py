import sys
from jinja2 import Environment, PackageLoader, TemplateNotFound, select_autoescape

from agentarena.core.exceptions import InvalidTemplateException
from agentarena.util.jinja_helpers import datetimeformat_filter


class JinjaRenderer:

    def __init__(self):
        self.env = Environment(
            loader=PackageLoader("agentarena"), autoescape=select_autoescape()
        )
        self.env.filters["datetimeformat"] = datetimeformat_filter

    def get_template(self, key: str):
        possibles = [key, f"{key}.md", f"{key}.md.j2"]
        try:
            return self.env.select_template(possibles)
        except TemplateNotFound as te:
            raise InvalidTemplateException(key)

    def render_template(self, key: str, data: dict) -> str:
        possibles = [key, f"{key}.md", f"{key}.md.j2"]
        try:
            template = self.env.select_template(possibles)
        except InvalidTemplateException as te:
            raise Exception(f"Could not find template {key}")

        return template.render(data)
