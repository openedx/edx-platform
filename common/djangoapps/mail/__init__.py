from django.core.mail import get_connection
from django.core.mail.message import EmailMultiAlternatives


def send_mail(subject, message, from_email, recipient_list,
              fail_silently=False, auth_user=None, auth_password=None,
              connection=None, html_message=None):
    """
    Note: this method is a copy of the django.core.mail.send_mail in v 1.7,
    which adds the html_message option.

    Easy wrapper for sending a single message to a recipient list. All members
    of the recipient list will see the other recipients in the 'To' field.

    If auth_user is None, the EMAIL_HOST_USER setting is used.
    If auth_password is None, the EMAIL_HOST_PASSWORD setting is used.

    Note: The API for this method is frozen. New code wanting to extend the
    functionality should use the EmailMessage class directly.
    """
    connection = connection or get_connection(username=auth_user,
                                    password=auth_password,
                                    fail_silently=fail_silently)
    mail = EmailMultiAlternatives(subject, message, from_email, recipient_list,
                                  connection=connection)
    if html_message:
        mail.attach_alternative(html_message, 'text/html')

    return mail.send()