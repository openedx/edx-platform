# pylint: disable=unused-import
"""
Python APIs exposed by the bulk_email app to other in-process apps.
"""

# Public Bulk Email Functions


from django.conf import settings
from django.urls import reverse

from lms.djangoapps.bulk_email.models_api import (
    is_bulk_email_disabled_for_course,
    is_bulk_email_enabled_for_course,
    is_bulk_email_feature_enabled,
    is_user_opted_out_for_course
)
from lms.djangoapps.discussion.notification_prefs.views import UsernameCipher
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


def get_emails_enabled(user, course_id):
    """
    Get whether or not emails are enabled in the context of a course.

    Arguments:
        user: the user object for which we want to check whether emails are enabled
        course_id (string): the course id of the course

    Returns:
        (bool): True if emails are enabled for the course associated with course_id for the user;
        False otherwise
    """
    if is_bulk_email_feature_enabled(course_id=course_id) and not is_bulk_email_disabled_for_course(course_id):
        return not is_user_opted_out_for_course(user=user, course_id=course_id)
    return None


def get_unsubscribed_link(username, course_id):
    """

    :param username: username
    :param course_id:
    :return: AES encrypted token based on the user email
    """
    lms_root_url = configuration_helpers.get_value('LMS_ROOT_URL', settings.LMS_ROOT_URL)
    token = UsernameCipher.encrypt(username)
    optout_url = reverse('bulk_email_opt_out', kwargs={'token': token, 'course_id': course_id})
    url = f'{lms_root_url}{optout_url}'
    return url
