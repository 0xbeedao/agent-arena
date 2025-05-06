"""
Dispatches results from the request_service to the appropriate controller.
"""

from agentarena.models.job import JsonRequestJob


class ResultService:

    def __init__(self, logger=None):
        self.log = logger.get_logger(module="resultservice")

    def send_payload(self, job: JsonRequestJob, payload: object):
        log = self.log.bind("method=send_payload")
        log.info("success", job=job, payload=payload)

    def send_rejection(self, job: JsonRequestJob, response: object):
        log = self.log.bind("method=send_rejection")
        log.info("failure", job=job, response=response)
