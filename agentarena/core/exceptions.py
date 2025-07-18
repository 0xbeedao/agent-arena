class InvalidTemplateException(Exception):
    pass


class TemplateRenderingException(Exception):
    """Exception raised when template rendering fails due to data issues"""

    def __init__(
        self,
        message: str,
        template_name: str,
        error_details: str,
        data_context: dict = None,
    ):
        self.message = message
        self.template_name = template_name
        self.error_details = error_details
        self.data_context = data_context or {}
        super().__init__(self.message)


class TemplateDataException(Exception):
    """Exception raised when template data is missing or invalid"""

    def __init__(
        self, message: str, missing_field: str = None, data_context: dict = None
    ):
        self.message = message
        self.missing_field = missing_field
        self.data_context = data_context or {}
        super().__init__(self.message)
