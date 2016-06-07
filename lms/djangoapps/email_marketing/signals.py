"""
This module contains signals needed for email integration
"""
import logging

from django.dispatch import receiver

from student.models import CourseEnrollment, UNENROLL_DONE
from student.views import REGISTER_USER
from email_marketing.models import EmailMarketingConfiguration
from util.model_utils import USER_FIELD_CHANGED
from lms.djangoapps.email_marketing.tasks import update_user, update_user_email

from sailthru.sailthru_client import SailthruClient
from sailthru.sailthru_error import SailthruClientError

log = logging.getLogger(__name__)

# list of changed fields to pass to Sailthru
CHANGED_FIELDNAMES = ['username', 'is_active', 'name', 'gender', 'education',
                      'age', 'level_of_education', 'year_of_birth',
                      'country']


@receiver(UNENROLL_DONE)
def handle_unenroll_done(sender, course_enrollment=None, skip_refund=False,
                         **kwargs):  # pylint: disable=unused-argument
    """
    Signal receiver for unenrollments
    """
    email_config = EmailMarketingConfiguration.current()
    if not email_config.enabled:
        return

    # TBD


@receiver(REGISTER_USER)
def email_marketing_register_user(sender, user=None, profile=None,
                                  **kwargs):  # pylint: disable=unused-argument
    """
    Called after user created and saved

    Args:
        sender: Not used
        user: The user object for the user being changed
        profile: The user profile for the user being changed
        kwargs: Not used
    """
    log.info("Receiving REGISTER_USER")
    email_config = EmailMarketingConfiguration.current()
    if not email_config.enabled:
        return

    # ignore anonymous users
    if user.is_anonymous():
        return

    # perform update asynchronously
    update_user.delay(user.username, new_user=True)


@receiver(USER_FIELD_CHANGED)
def email_marketing_user_field_changed(sender, user=None, table=None, setting=None,
                                       old_value=None, new_value=None, **kwargs):  # pylint: disable=unused-argument
    """
    Update a single user/profile field

    Args:
        sender: Not used
        user: The user object for the user being changed
        table: The name of the table being updated
        setting: The name of the setting being updated
        old_value: Prior value
        new_value: New value
        kwargs: Not used
    """
    email_config = EmailMarketingConfiguration.current()
    if not email_config.enabled:
        return

    # ignore anonymous users
    if user.is_anonymous():
        return

    # ignore anything but User or Profile table
    if table != 'auth_user' and table != 'auth_userprofile':
        return

    # ignore anything not in list of fields to handle
    if setting in CHANGED_FIELDNAMES:
        # perform update asynchronously, flag if activation
        update_user.delay(user.username, new_user=False,
                          activation=(setting == 'is_active') and new_value is True)

    elif setting == 'email':
        # email update is special case
        update_user_email.delay(user.username, old_value)
