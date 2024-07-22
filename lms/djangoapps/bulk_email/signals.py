"""
Signal handlers for the bulk_email app
"""
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from eventtracking import tracker

from common.djangoapps.student.models import CourseEnrollment
from openedx.core.djangoapps.user_api.accounts.signals import USER_RETIRE_MAILINGS
from edx_ace.signals import ACE_EMAIL_SENT

from .models import Optout


@receiver(USER_RETIRE_MAILINGS)
def force_optout_all(sender, **kwargs):  # lint-amnesty, pylint: disable=unused-argument
    """
    When a user is retired from all mailings this method will create an Optout
    row for any courses they may be enrolled in.
    """
    user = kwargs.get('user', None)

    if not user:
        raise TypeError('Expected a User type, but received None.')

    for enrollment in CourseEnrollment.objects.filter(user=user):
        Optout.objects.get_or_create(user=user, course_id=enrollment.course.id)


@receiver(ACE_EMAIL_SENT)
def ace_email_sent_handler(sender, **kwargs):
    """
    When an email is sent using ACE, this method will create an event to detect ace email success status
    """
    # Fetch the message object from kwargs, defaulting to None if not present
    message = kwargs.get('message', None)

    # Check if message is not None and has the attribute 'message_type'
    if message and hasattr(message, 'name') and message.name == 'bulkemail':
        user_model = get_user_model()
        try:
            user_id = user_model.objects.get(email=message.recipient.email_address).id
        except user_model.DoesNotExist:
            user_id = None

        tracker.emit(
            'edx.bulk_email.sent',
            {
                'message_type': message.name,
                'course_id': str(message.context['course_email'].course_id),
                'user_id': user_id,
            }
        )
