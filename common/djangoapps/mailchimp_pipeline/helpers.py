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
    course_keys = []
    for enrollment in get_enrollments(username):
        course_key = CourseKey.from_string(enrollment.get('course_details', {}).get('course_id', ''))
        course_keys.append(course_key)

    enrollment_coruse_short_id = ",".join(
        [str(c.course_short_id) for c in CustomSettings.objects.filter(id__in=course_keys)]
    )

    return enrollment_coruse_short_id


def get_org_data_for_mandrill(organization):
    org_label = ""
    org_type = ""
    focus_area = ""

    if organization:
        focus_areas = FocusArea.get_map()
        org_sectors = OrgSector.get_map()
        org_label = organization.label if organization else ""

        org_type = ""
        if organization.org_type:
            org_type = org_sectors.get(organization.org_type, "")

        focus_area = str(focus_areas.get(organization.focus_area, "")) if organization else ""

    return org_label, org_type, focus_area
