from jinja2 import Environment
from jinja2 import PackageLoader
from jinja2 import TemplateNotFound
from jinja2 import select_autoescape
from jinja2.exceptions import UndefinedError
from jinja2.exceptions import TemplateError

from agentarena.core.exceptions import InvalidTemplateException
from agentarena.core.exceptions import TemplateRenderingException
from agentarena.core.exceptions import TemplateDataException
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
        if key.lower() != key:
            possibles.append(key.lower())
            possibles.append(f"{key.lower()}.md")
            possibles.append(f"{key.lower()}.md.j2")

        try:
            return self.env.select_template(possibles)
        except TemplateNotFound as te:
            raise InvalidTemplateException(key)

    def render_template(self, key: str, data: dict) -> str:
        possibles = [key, f"{key}.j2", f"{key}.md", f"{key}.md.j2"]
        if key.lower() != key:
            possibles.append(key.lower())
            possibles.append(f"{key.lower()}.md")
            possibles.append(f"{key.lower()}.md.j2")

        try:
            template = self.env.select_template(possibles)
        except InvalidTemplateException as te:
            raise Exception(f"Could not find template {key}")

        try:
            return template.render(data)
        except UndefinedError as e:
            # Handle specific Jinja2 undefined errors
            error_msg = str(e)
            if "list object has no element" in error_msg:
                # Extract the problematic field from the error message
                # e.g., "list object has no element 0" -> trying to access index 0 of an empty list
                raise TemplateDataException(
                    message=f"Template data error: {error_msg}",
                    missing_field=error_msg,
                    data_context={"template": key, "data_keys": list(data.keys())},
                )
            elif "object has no attribute" in error_msg:
                # Handle missing attribute errors
                raise TemplateDataException(
                    message=f"Template data error: {error_msg}",
                    missing_field=error_msg,
                    data_context={"template": key, "data_keys": list(data.keys())},
                )
            else:
                # Generic undefined error
                raise TemplateRenderingException(
                    message=f"Template rendering failed: {error_msg}",
                    template_name=key,
                    error_details=error_msg,
                    data_context={"data_keys": list(data.keys())},
                )
        except TemplateError as e:
            # Handle other Jinja2 template errors
            raise TemplateRenderingException(
                message=f"Template rendering failed: {str(e)}",
                template_name=key,
                error_details=str(e),
                data_context={"data_keys": list(data.keys())},
            )
        except Exception as e:
            # Handle any other unexpected errors
            raise TemplateRenderingException(
                message=f"Unexpected error during template rendering: {str(e)}",
                template_name=key,
                error_details=str(e),
                data_context={"data_keys": list(data.keys())},
            )
