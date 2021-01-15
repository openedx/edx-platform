"""
Client for Sending email via mandrill
"""

import logging

import mandrill
from django.conf import settings

log = logging.getLogger(__name__)


class MandrillClient(object):
    """
    Mandrill Client for handling the basic send mail feature
    """
    ACUMEN_DATA_TEMPLATE = 'acumen-data'
    PASSWORD_RESET_TEMPLATE = 'template-60'
    PASSWORD_RESET_COMPLETE = 'reset-password-complete'
    USER_ACCOUNT_ACTIVATION_TEMPLATE = 'template-61'
    ORG_ADMIN_ACTIVATION_TEMPLATE = 'org-admin-identified'
    ORG_ADMIN_CHANGE_TEMPLATE = 'org-admin-change'
    ORG_ADMIN_GET_IN_TOUCH = 'org-admin-get-in-touch'
    ORG_ADMIN_CLAIM_CONFIRMATION = 'org-admin-claim-confirmation'
    NEW_ADMIN_CLAIM_CONFIRMATION = 'org-admin-update-confirmation'
    NEW_ADMIN_GET_IN_TOUCH = 'new-admin-get-in-touch'
    ENROLLMENT_CONFIRMATION_TEMPLATE = 'enrollment-confirmation'
    ENROLLMENT_CONFIRMATION_TEST_TEMPLATE = 'test-template'
    COURSE_WELCOME_TEMPLATE = 'course-welcome'
    COURSE_EARLY_WELCOME_TEMPLATE = 'course-early-welcome'
    COURSE_START_REMINDER_TEMPLATE = 'course-start-reminder'
    COURSE_COMPLETION_TEMPLATE = 'course-completion'
    REMIND_LEARNERS_TEMPLATE = 'remind-learners'
    COURSE_INVITATION_ONLY_REGISTER_TEMPLATE = 'course-invitation-only-register-user'
    ALQUITY_FAKE_SUBMIT_CONFIRMATION_TEMPLATE = 'alquity-fake-submit-confirmation'
    COURSE_ACTIVATION_REMINDER_TEMPLATE = 'activation-reminder'
    ON_DEMAND_SCHEDULE_EMAIL_TEMPLATE = 'on-demand-course-schedule'
    ON_DEMAND_WEEKLY_MODULE_COMPLETE_TEMPLATE = 'module-completion-weekly-email'
    ON_DEMAND_WEEKLY_MODULE_SKIP_TEMPLATE = 'on-demand-module-skip'
    ON_DEMAND_REMINDER_EMAIL_TEMPLATE = 'on-demand-reminder-email'
    CHANGE_USER_EMAIL_ALERT = 'change-user-email-alert'
    VERIFY_CHANGE_USER_EMAIL = 'verify-email-change'
    DOWNLOAD_CERTIFICATE = 'download-certificate'
    USER_BADGE_EMAIL_TEMPLATE = 'user-badge-email'
    REFERRAL_INITIAL_EMAIL = 'referral-email'
    REFERRAL_FOLLOW_UP_EMAIL = 'referred-learner-follow-up'
    REFERRAL_SOCIAL_IMPACT_TOOLKIT = 'social-impact-toolkit'
    MINI_COURSE_ENROLMENT = 'mini-course-enrolment'
    SEND_ACTION_PLAN = 'send-action-plan'

    def __init__(self):
        self.mandrill_client = mandrill.Mandrill(settings.MANDRILL_API_KEY)

    def get_receiver_emails(self, receiver_emails_string):
        """
        Parsing the comma separated email to a list of receiver emails

        Arguments:
            receiver_emails_string: String contains a comma separated emails

        Returns:
            receiver_emails (list): A list of receiver emails
        """
        email_list = receiver_emails_string.split(',')
        receiver_emails = [{'email': email} for email in email_list]
        return receiver_emails

    def send_mail(self, template_name, receiver_emails_string, context, attachments=None, subject=None,
                  reply_to_email=None, images=None):
        """
        calls the mandrill API for the specific template and email

        arguments:
        template_name: the slug/identifier of the mandrill email template
        receiver_emails_string: the email or comma separated emails of the receiver's
        context: the data which is passed to the template. must be a dict
        attachments: list of file attachments
        Subject: A subject  title for email
        reply_to_email:  email for reply_to
        images: images attachments for referring it from content of email template
        """
        images = images or []
        attachments = attachments or []
        global_merge_vars = [{'name': key, 'content': context[key]} for key in context]

        message = {
            'from_email': settings.NOTIFICATION_FROM_EMAIL,
            'to': self.get_receiver_emails(receiver_emails_string),
            'global_merge_vars': global_merge_vars,
            'attachments': attachments,
            'images': images,
        }

        if subject:
            message.update({'subject': subject})

        if reply_to_email:
            message.update({'headers': {'Reply-To': reply_to_email}})

        try:
            result = self.mandrill_client.messages.send_template(
                template_name=template_name,
                template_content=[],
                message=message,
            )
            log.info('A mandrill info:  {result}'.format(result=result))
        except mandrill.Error as e:
            # Mandrill errors are thrown as exceptions
            log.error('A mandrill error occurred: {eClass} - {error}'.format(eClass=e.__class__, error=e))
            raise
        return result
