"""
Email data contains all data related to email.
"""

from django.conf import settings


class EmailData(object):
    """
    Email data class that contains all data related to email
    """

    def __init__(self, template_name, useer_email, context, subject=None, attachments=None):
        self.template_name = template_name
        global_merge_vars = [{'name': key, 'content': context[key]} for key in context]

        self.message = {
            'from_email': settings.NOTIFICATION_FROM_EMAIL,
            'to': [{'email': useer_email}],
            'global_merge_vars': global_merge_vars,
            'attachments': attachments or [],
        }

        if subject:
            self.message.update({'subject': subject})
