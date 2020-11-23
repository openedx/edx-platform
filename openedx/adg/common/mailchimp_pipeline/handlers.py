"""
Signals for Mailchimp pipeline
"""
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from openedx.adg.lms.utils.decorators import suspendingreceiver
from student.models import EnrollStatusChange
from student.signals import ENROLL_STATUS_CHANGE

from .tasks import task_send_user_enrollments_to_mailchimp, task_send_user_info_to_mailchimp


@suspendingreceiver(post_save, sender=User)
def send_user_info_to_mailchimp(sender, created, **kwargs):  # pylint: disable=unused-argument
    """
    Listen for user update or creation and call task for syncing user with Mailchimp.

    Args:
        sender (obj): The sender of the signal
        created (boolean): True if user object is created, False if user updated
        **kwargs (dict): Additional parameters

    Returns:
        None
    """
    if not created:
        return  # TODO LP-2446 Handle not created case

    task_send_user_info_to_mailchimp(**kwargs)


@suspendingreceiver(ENROLL_STATUS_CHANGE)
def send_user_enrollments_to_mailchimp(sender, event=None, **kwargs):  # pylint: disable=unused-argument
    """
    Listen for course enrollment events (enrollment and un-enrollment) and call task for syncing enrollment
    with Mailchimp.

    Args:
        sender (obj): The sender of the signal
        event (string): Signal name
        **kwargs (dict): Additional parameters

    Returns:
        None
    """
    if event not in [EnrollStatusChange.enroll, EnrollStatusChange.unenroll]:
        return

    task_send_user_enrollments_to_mailchimp(**kwargs)
