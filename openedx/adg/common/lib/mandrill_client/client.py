"""
Mandrill Client to send ADG emails
"""
import logging

import mandrill
from django.conf import settings

from .email_data import EmailData
from .helpers import mandrill_exception_handler_decorator

log = logging.getLogger(__name__)


class MandrillClient(object):
    """
    Mandrill class to send ADG emails

    Note: While adding here, language is trimmed from the template slug
    For example on mandrill if we have 'adg-password-reset' for English and 'adg-password-reset-ar' for Arabic
    here it would be defined as 'adg-password-reset'
    """
    CHANGE_USER_EMAIL_ALERT = 'adg-confirm-email-address-change'
    COURSE_ENROLLMENT_INVITATION = 'adg-invitation-course'
    ENROLLMENT_CONFIRMATION = 'adg-enrollment-confirmation'
    PASSWORD_RESET = 'adg-password-reset'
    PASSWORD_RESET_SUCCESS = 'reset-password-success'
    USER_ACCOUNT_ACTIVATION = 'adg-user-activation-email'
    VERIFY_CHANGE_USER_EMAIL = 'adg-verify-email-address-change-step-2'
    APPLICATION_SUBMISSION_CONFIRMATION = 'adg-application-submission-confirmation-1'
    APPLICATION_WAITLISTED = 'adg-waitlisted-application'
    APPLICATION_ACCEPTED = 'adg-application-accepted'
    WEBINAR_CANCELLATION = 'adg-cancellation-email'
    WEBINAR_REGISTRATION_CONFIRMATION = 'adg-webinar-confirmation'
    WEBINAR_ONE_WEEK_REMINDER = 'adg-reminder-email-1-week'
    WEBINAR_TWO_HOURS_REMINDER = 'adg-reminder-email'
    WEBINAR_CREATED = 'adg-webinar-invite'
    WEBINAR_UPDATED = 'adg-webinar-update-email'

    def __init__(self):
        self.mandrill_client = mandrill.Mandrill(settings.MANDRILL_API_KEY)

    @mandrill_exception_handler_decorator(False)
    def cancel_scheduled_email(self, msg_id):
        """
        Calls the mandrill API to cancel a scheduled email.

        Args:
            msg_id (str): Scheduled email Id.

        Returns:
            dict: dictionary containing mandrill response
        """
        return self.mandrill_client.messages.cancel_scheduled(msg_id)

    @mandrill_exception_handler_decorator(True)
    def reschedule_email(self, msg_id, send_at):
        """
        Calls mandrill API to reschedule an email.

        Args:
            msg_id (str): Mandrill msg id of the scheduled email.
            send_at (str): String containing time to reschedule at.

        Returns:
            dict: Dictionary containing mandrill response.
        """
        return self.mandrill_client.messages.reschedule(msg_id, send_at)

    @mandrill_exception_handler_decorator(True)
    def list_scheduled_emails(self, email):
        """
        Lists all scheduled messages for an email address.

        Args:
            email (str): Email address for which list will be fetched.

        Returns:
            list: List of scheduled emails for a user email.
        """
        return self.mandrill_client.messages.list_scheduled(email)

    @mandrill_exception_handler_decorator(True)
    def _send_mail(self, email_data, send_at=None):
        """
        Calls the mandrill API for the specific template and email

        Arguments:
            email_data (EmailData): All the data related to email
            send_at (str): A String containing the time at which email will be sent

        Returns:
            list: list of dictionaries containing mandrill responses
        """
        return self.mandrill_client.messages.send_template(
            template_name=email_data.template_name,
            template_content=[],
            message=email_data.message,
            send_at=send_at
        )

    def send_mandrill_email(self, template, emails, context, send_at=None):
        """
        Creates EmailData object and calls _send_email

        Arguments:
            template (str): String containing template id
            emails (list): Email addresses of recipient users
            context (dict): Dictionary containing email content
            send_at (str): A String containing the time at which email will be sent

        Returns:
            list: list of dictionaries containing mandrill responses
        """
        log.info(f'Sending email using template: {template}, account: {emails} and context: {context} using mandrill')
        email_data = EmailData(template, emails, context)
        return self._send_mail(email_data, send_at)
