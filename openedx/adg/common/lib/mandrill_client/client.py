"""
Mandrill Client to send ADG emails
"""
import logging

import mandrill
from django.conf import settings

log = logging.getLogger(__name__)


class MandrillClient(object):
    """
    Mandrill class to send ADG emails
    """
    APPLICATION_SUBMISSION_CONFIRMATION_TEMPLATE = 'adg-application-submission-confirmation'

    def __init__(self):
        self.mandrill_client = mandrill.Mandrill(settings.MANDRILL_API_KEY)

    def send_mail(self, email_data):
        """
        Calls the mandrill API for the specific template and email

        Arguments:
            email_data (EmailData): all the data related to email

        Returns:
            list: list of dictionaries containing mandrill responses
        """
        try:
            result = self.mandrill_client.messages.send_template(
                template_name=email_data.template_name,
                template_content=[],
                message=email_data.message,
            )
            log.info(result)
        except mandrill.Error as e:
            log.error('A mandrill error occurred: {exception_class} - {exception}'.format(
                exception_class=e.__class__, exception=e)
            )
            raise
        return result
