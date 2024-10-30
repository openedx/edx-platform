"""
Signal handlers for the bulk_email app
"""
from django.dispatch import receiver
from eventtracking import tracker

from common.djangoapps.student.models import CourseEnrollment
from openedx.core.djangoapps.user_api.accounts.signals import USER_RETIRE_MAILINGS
from edx_ace.signals import ACE_MESSAGE_SENT

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


@receiver(ACE_MESSAGE_SENT)
def ace_email_sent_handler(sender, **kwargs):
    """
    When an email is sent using ACE, this method will create an event to detect ace email success status
    """
    # Fetch the message dictionary from kwargs, defaulting to {} if not present
    message = kwargs.get('message', {})
    recipient = message.get('recipient', {})
    message_name = message.get('name', None)
    context = message.get('context', {})
    email_address = recipient.get('email', None)
    user_id = recipient.get('user_id', None)
    channel = message.get('channel', None)
    course_id = context.get('course_id', None)
    if not course_id:
        course_email = context.get('course_email', None)
        course_id = course_email.course_id if course_email else None

    tracker.emit(
        'edx.ace.message_sent',
        {
            'message_type': message_name,
            'channel': channel,
            'course_id': course_id,
            'user_id': user_id,
            'user_email': email_address,
        }
    )
