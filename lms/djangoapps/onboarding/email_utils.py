from django.core import mail
from django.conf import settings

from smtplib import SMTPException

def send_admin_activation_email(subject, message, from_address, dest_addr):
    """
    Send an admin activation email.
    """
    max_retries = settings.RETRY_ACTIVATION_EMAIL_MAX_ATTEMPTS

    while max_retries > 0:
        try:
            mail.send_mail(subject, message, from_address, [dest_addr], fail_silently=False)
            max_retries = 0
        except SMTPException:
            max_retries -= 1
        except Exception:
            max_retries -= 1
