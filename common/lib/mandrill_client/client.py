import mandrill

from django.conf import settings

class MandrillClient:
    mandrill_client = mandrill.Mandrill(settings.MANDRILL_API_KEY)

    @classmethod
    def send_activation_mail(cls, user_email, message, context):
        try:
            result = cls.mandrill_client.messages.send_template(
                template_name='template-61',
                template_content=[
                    {'name': 'name', 'content': context['name']},
                    {'name': 'key', 'content': context['key']},
                ],
                message={
                    'from_email': settings.NOTIFICATION_FROM_EMAIL,
                    'text': 'Welcome to PhilU',
                    'to': [{ 'email': user_email }],
                    'global_merge_vars': [
                        {'name': 'name', 'content': context['name']},
                        {'name': 'key', 'content': context['key']},

                    ]
                },
            )
            print result
        except mandrill.Error, e:
            # Mandrill errors are thrown as exceptions
            print 'A mandrill error occurred: %s - %s' % (e.__class__, e)
            # A mandrill error occurred: <class 'mandrill.UnknownSubaccountError'> - No subaccount exists with the id 'customer-123'
            raise
