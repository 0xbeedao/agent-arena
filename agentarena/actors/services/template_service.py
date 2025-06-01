from jinja2 import Environment
from jinja2 import PackageLoader
from jinja2 import TemplateNotFound
from jinja2 import select_autoescape

from agentarena.core.factories.logger_factory import LoggingService


class TemplateService:
    """
    Provides template filling services, using Jinja2
    """

    def __init__(self, logging: LoggingService):
        self.log = logging.get_logger("service")
        self.env = Environment(
            loader=PackageLoader("agentarena.actors"), autoescape=select_autoescape()
        )
        self.log.debug("Found templates", templates=self.env.list_templates())

    def get_template(self, key: str):
        possibles = [key, f"{key}.md", f"{key}.md.j2"]
        try:
            return self.env.select_template(possibles)
        except TemplateNotFound as te:
            self.log.error("could not find template", key=key)
            raise te

    def render_template(self, key, **kwargs):
        """
        Render the template by key, with the kwargs as values
        """
        return self.get_template(key).render(**kwargs)
