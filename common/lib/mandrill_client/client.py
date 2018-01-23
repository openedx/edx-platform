import mandrill
import logging

from django.conf import settings

log = logging.getLogger(__name__)

class MandrillClient(object):
    def __init__(self):
        self.mandrill_client = mandrill.Mandrill(settings.MANDRILL_API_KEY)

    def send_template(self, template_name, user_email, global_merge_vars):
        try:
            result = self.mandrill_client.messages.send_template(
                template_name=template_name,
                template_content=[],
                message={
                    'from_email': settings.NOTIFICATION_FROM_EMAIL,
                    'to': [{ 'email': user_email }],
                    'global_merge_vars': global_merge_vars
                },
            )
            log.info(result)
        except mandrill.Error, e:
            # Mandrill errors are thrown as exceptions
            log.error('A mandrill error occurred: %s - %s' % (e.__class__, e))
            # A mandrill error occurred: <class 'mandrill.UnknownSubaccountError'> - No subaccount exists with the id 'customer-123'
            raise
        return result

    def send_activation_mail(self, user_email, context):
        global_merge_vars = [
            {'name': 'first_name', 'content': context['first_name']},
            {'name': 'activation_link', 'content': context['key']},
        ]
        self.send_template('template-61', user_email, global_merge_vars)

    def send_admin_activation_mail(self, user_email, context):
        """
        E-mail is sent only when a user is recommended is and org admin
        """
        global_merge_vars = [
            {'name': 'first_name', 'content': context['first_name']},
            {'name': 'activation_link', 'content': context['key']},
            {'name': 'org_id', 'content': context['org_id']},
            {'name': 'org_name', 'content': context['org_name']},
            {'name': 'referring_user', 'content': context['referring_user']},
        ]
        self.send_template('template-62', user_email, global_merge_vars)


    def send_password_reset_email(self, user_email, context):
        global_merge_vars = [
            {'name': 'first_name', 'content': context['first_name']},
            {'name': 'reset_link', 'content': context['reset_link']},
        ]
        self.send_template('template-60', user_email, global_merge_vars)

    def send_course_notification_email(self, user_email, template_name, context):
        """
        single function to use for all notifications regarding any course email
        template_name must be specified
        """
        global_merge_vars = [
            {'name': 'full_name', 'content': context['full_name']},
            {'name': 'course_name', 'content': context['course_name']},
            {'name': 'course_url', 'content': context['course_link']},
        ]
        self.send_template(template_name, user_email, global_merge_vars)

