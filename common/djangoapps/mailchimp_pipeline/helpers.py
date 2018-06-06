from datetime import datetime
import pytz
from lms.djangoapps.onboarding.models import (FocusArea, OrgSector, )


def is_active_enrollment(course_end_date):
    """Check if enrollment is still active"""
    if course_end_date:
        return datetime.now(pytz.timezone("UTC")) < course_end_date

    return False


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
