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
    CHANGE_USER_EMAIL_ALERT = 'adg-confirm-email-address-change'
    COURSE_ENROLLMENT_INVITATION = 'course-enrollment-invitation'
    ENROLLMENT_CONFIRMATION = 'adg-enrollment-confirmation'
    PASSWORD_RESET = 'adg-password-reset'
    USER_ACCOUNT_ACTIVATION = 'adg-user-activation-email'
    VERIFY_CHANGE_USER_EMAIL = 'adg-verify-email-address-change-step-2'

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
