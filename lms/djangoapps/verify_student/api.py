"""
API module.
"""
import logging

from django.conf import settings
from django.utils.translation import gettext as _

from lms.djangoapps.verify_student.emails import send_verification_approved_email
from lms.djangoapps.verify_student.exceptions import VerificationAttemptInvalidStatus
from lms.djangoapps.verify_student.models import VerificationAttempt
from lms.djangoapps.verify_student.statuses import VerificationAttemptStatus
from lms.djangoapps.verify_student.tasks import send_verification_status_email

log = logging.getLogger(__name__)


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

    This method is intended to be used by IDV implementation plugins to create VerificationAttempt instances.

    Args:
        user (User): the user (usually a learner) performing the verification attempt
        name (string): the name being ID verified
        status (string): the initial status of the verification attempt
        expiration_datetime (datetime, optional): When the verification attempt expires. Defaults to None.

    Returns:
        id (int): The id of the created VerificationAttempt instance
    """
    verification_attempt = VerificationAttempt.objects.create(
        user=user,
        name=name,
        status=status,
        expiration_datetime=expiration_datetime,
    )

    return verification_attempt.id


def update_verification_attempt(attempt_id, name=None, status=None, expiration_datetime=None):
    """
    Update a verification attempt.

    This method is intended to be used by IDV implementation plugins to update VerificationAttempt instances.

    Arguments:
        * attempt_id (int): the verification attempt id of the attempt to update
        * name (string, optional): the new name being ID verified
        * status (string, optional): the new status of the verification attempt
        * expiration_datetime (datetime, optional): The new expiration date and time

    Returns:
        * None
    """
    try:
        attempt = VerificationAttempt.objects.get(id=attempt_id)
    except VerificationAttempt.DoesNotExist:
        log.error(
            f'VerificationAttempt with id {attempt_id} was not found '
            f'when updating the attempt to status={status}',
        )
        raise

    if name is not None:
        attempt.name = name

    if status is not None:
        attempt.status = status

        status_list = [attr for attr in dir(VerificationAttemptStatus) if not attr.startswith('__')]
        if status not in status_list:
            log.error(
                'Attempted to call update_verification_attempt called with invalid status: %(status)s. '
                'Status must be one of: %(status_list)s',
                {
                    'status': status,
                    'status_list': VerificationAttempt.STATUS_CHOICES,
                },
            )
            raise VerificationAttemptInvalidStatus

    if expiration_datetime is not None:
        attempt.expiration_datetime = expiration_datetime

    attempt.save()
