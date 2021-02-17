"""
Helpers to provide utility to the mailchimp_pipeline app
"""
from datetime import datetime
import pytz
from custom_settings.models import CustomSettings
from enrollment.api import get_enrollments
from opaque_keys.edx.keys import CourseKey
from lms.djangoapps.onboarding.models import (FocusArea, OrgSector, )


def is_active_enrollment(course_end_date):
    """Check if enrollment is still active"""
    if course_end_date:
        return datetime.now(pytz.timezone("UTC")) < course_end_date

    return False


def get_user_active_enrollements(username):
    return ", ".join([enrollment.get('course_details', {}).get('course_name', '')
                      for enrollment in get_enrollments(username)
                      if is_active_enrollment(enrollment.get('course_details', {}).get('course_end', ''))])


def get_enrollements_course_short_ids(username):
    """
    Get the short course ids for all the enrollments of a given username

    Arguments:
        username (str): Username to get the enrollments' short course ids for

    Returns:
        str: All the short course ids (comma separated) associated with the enrollments of the given username
    """
    course_keys = []
    for enrollment in get_enrollments(username):
        course_key = CourseKey.from_string(enrollment.get('course_details', {}).get('course_id', ''))
        course_keys.append(course_key)

    enrollment_coruse_short_id = ",".join(
        [str(c.course_short_id) for c in CustomSettings.objects.filter(id__in=course_keys)]
    )

    return enrollment_coruse_short_id


def get_org_data_for_mandrill(organization):
    """
    Get all the details associated with an organization

    Arguments:
        organization: Target organization

    Returns:
        (str, str, str): The label, type, and the focus area of the target organization respectively in a tuple
    """
    org_label = org_type = focus_area = ""

    if organization:

        org_label = organization.label
        org_type = OrgSector.objects.get_map().get(organization.org_type, "")
        focus_area = FocusArea.get_map().get(organization.focus_area, "")

    return org_label, org_type, focus_area
