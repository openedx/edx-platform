"""
Email data contains all data related to email.
"""

from django.conf import settings


class EmailData(object):
    """
    Email data class that contains all data related to email
    """

    def __init__(self, template_name, recipient_emails, context, subject=None, attachments=None):
        self.template_name = template_name
        global_merge_vars = [{'name': key, 'content': context[key]} for key in context]

        self.message = {
            'from_email': settings.NOTIFICATION_FROM_EMAIL,
            'to': recipient_emails,
            'global_merge_vars': global_merge_vars,
            'attachments': attachments or [],
        }

        if subject:
            self.message.update({'subject': subject})
