"""
Signals for Mailchimp pipeline
"""
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from openedx.adg.lms.utils.decorators import suspendingreceiver
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import EnrollStatusChange
from student.signals import ENROLL_STATUS_CHANGE

from .helpers import send_user_enrollments_to_mailchimp, send_user_info_to_mailchimp


@suspendingreceiver(post_save, sender=User)
def listen_for_auth_user_model(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Listen for new user creation

    Args:
        sender (obj): The sender of the signal
        **kwargs (dict): Additional parameters

    Returns:
        None
    """
    created = 'created' in kwargs and kwargs['created']
    user = kwargs['instance']
    send_user_info_to_mailchimp(user, created)


@suspendingreceiver(ENROLL_STATUS_CHANGE)
def listen_for_user_enrollments(sender, event=None, user=None, **kwargs):  # pylint: disable=unused-argument
    """
    Listen for course enrollment events, specially enrollment and un-enrollment

    Args:
        sender (obj): The sender of the signal
        event (string): Signal name
        user (User): The user object, related to signal
        **kwargs (dict): Additional parameters

    Returns:
        None
    """
    if event not in [EnrollStatusChange.enroll, EnrollStatusChange.unenroll]:
        return

    course_id = kwargs.get('course_id')
    course = CourseOverview.objects.get(id=course_id)
    send_user_enrollments_to_mailchimp(user, course)
