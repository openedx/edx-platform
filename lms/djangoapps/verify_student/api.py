"""
API module.
"""
from django.conf import settings
from django.utils.translation import gettext as _

from lms.djangoapps.verify_student.emails import send_verification_approved_email
from lms.djangoapps.verify_student.models import VerificationAttempt
from lms.djangoapps.verify_student.tasks import send_verification_status_email


def send_approval_email(attempt):
    """
    Send an approval email to the learner associated with the IDV attempt.
    """
    verification_status_email_vars = {
        'platform_name': settings.PLATFORM_NAME,
    }

    expiration_datetime = attempt.expiration_datetime.date()
    if settings.VERIFY_STUDENT.get('USE_DJANGO_MAIL'):
        verification_status_email_vars['expiration_datetime'] = expiration_datetime.strftime("%m/%d/%Y")
        verification_status_email_vars['full_name'] = attempt.user.profile.name
        subject = _("Your {platform_name} ID verification was approved!").format(
            platform_name=settings.PLATFORM_NAME
        )
        context = {
            'subject': subject,
            'template': 'emails/passed_verification_email.txt',
            'email': attempt.user.email,
            'email_vars': verification_status_email_vars
        }
        send_verification_status_email.delay(context)
    else:
        email_context = {'user': attempt.user, 'expiration_datetime': expiration_datetime.strftime("%m/%d/%Y")}
        send_verification_approved_email(context=email_context)


def create_verification_attempt(user, name, status, expiration_datetime=None):
    """
    Create a verification attempt.

    Args:
        user (User): the user (usually a learner) performing the verfication attempt
        name (string): the name of the user
        status (string): the initial status of the verification attempt
        expiration_datetime (datetime, optional): When the verification attempt expires. Defaults to None.

    Returns:
        VerificationAttempt (VerificationAttempt): The created VerificationAttempt instance
    """
    verification_attempt = VerificationAttempt.objects.create(
        user=user,
        name=name,
        status=status,
        expiration_datetime=expiration_datetime,
    )

    return verification_attempt.id


def update_verification_status(attempt_id, status):
    """
    Update the VerificationAttempt status.

    Arguments:
        * id (str): the verification attempt id
        * status (str): the new status

    Returns:
        * None
    """
    attempt = VerificationAttempt.objects.get(id=attempt_id)
    attempt.status = status
    attempt.save()
