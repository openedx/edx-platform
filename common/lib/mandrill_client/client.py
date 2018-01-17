import mandrill
import logging

from django.conf import settings

log = logging.getLogger(__name__)

class MandrillClient(object):
    def __init__(self):
        self.mandrill_client = mandrill.Mandrill(settings.MANDRILL_API_KEY)

    def send_activation_mail(self, user_email, context):
        try:
            result = self.mandrill_client.messages.send_template(
                template_name='template-61',
                template_content=[],
                message={
                    'from_email': settings.NOTIFICATION_FROM_EMAIL,
                    'to': [{ 'email': user_email }],
                    'global_merge_vars': [
                        {'name': 'name', 'content': context['name']},
                        {'name': 'key', 'content': context['key']},
                    ]
                },
            )
            log.info(result)
        except mandrill.Error, e:
            # Mandrill errors are thrown as exceptions
            log.error('A mandrill error occurred: %s - %s' % (e.__class__, e))
            # A mandrill error occurred: <class 'mandrill.UnknownSubaccountError'> - No subaccount exists with the id 'customer-123'
            raise

    def send_password_reset_email(self, user_email, context):
        try:
            result = self.mandrill_client.messages.send_template(
                template_name='template-60',
                template_content=[],
                message={
                    'from_email': settings.NOTIFICATION_FROM_EMAIL,
                    'to': [{ 'email': user_email }],
                    'global_merge_vars': [
                        {'name': 'password_reset_link', 'content': context['password_reset_link']},
                    ]
                },
            )
            log.info(result)
        except mandrill.Error, e:
            # Mandrill errors are thrown as exceptions
            log.error('A mandrill error occurred: %s - %s' % (e.__class__, e))
            # A mandrill error occurred: <class 'mandrill.UnknownSubaccountError'> - No subaccount exists with the id 'customer-123'
            raise

    def send_course_notification_email(self, user_email, context):
        try:
            result = self.mandrill_client.messages.send_template(
                template_name='enrollment-confirmation',
                template_content=[],
                message={
                    'from_email': settings.NOTIFICATION_FROM_EMAIL,
                    'to': [{ 'email': user_email }],
                    'global_merge_vars': [
                        {'name': 'course_name', 'content': context['course_name']},
                        {'name': 'course_link', 'content': context['course_link']},
                    ]
                },
            )
            log.info(result)
        except mandrill.Error, e:
            # Mandrill errors are thrown as exceptions
            log.error('A mandrill error occurred: %s - %s' % (e.__class__, e))
            # A mandrill error occurred: <class 'mandrill.UnknownSubaccountError'> - No subaccount exists with the id 'customer-123'
            raise


