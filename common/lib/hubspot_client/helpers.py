"""
HubSpot helpers.
"""
import logging

from mailchimp_pipeline.helpers import (
    get_enrollements_course_short_ids,
    get_user_active_enrollements
)

log = logging.getLogger(__name__)


def prepare_user_data_for_hubspot_contact_creation(user):
    """
    Generates user JSON to create contact on HubSpot.
    """
    user_json = {
        'properties': {
            'edx_full_name': user.get_full_name(),
            'email': user.email,
            'edx_username': user.username,
            'edx_marketing_opt_in': 'subscribed',
            'date_registered': str(user.date_joined.strftime('%m/%d/%Y'))
        }
    }

    extended_profile = user.extended_profile if hasattr(user, 'extended_profile') else None
    if extended_profile and extended_profile.organization:
        org_label, org_type, work_area = extended_profile.organization.hubspot_data()
        user_json['properties'].update(
            {
                'edx_organization': org_label,
                'edx_organization_type': org_type,
                'edx_area_of_work': work_area
            }
        )

    profile = user.profile if hasattr(user, 'profile') else None
    if profile and (profile.language or profile.country or profile.city):
        user_json['properties'].update(
            {
                'edx_language': profile.language or '',
                'edx_country': profile.country.name.format() if extended_profile.country else '',
                'edx_city': profile.city or '',
            }
        )

    log.info("-------------------------\n fetching enrollments \n ------------------------------\n")

    enrollment_titles = get_user_active_enrollements(user.username)
    enrollment_short_ids = get_enrollements_course_short_ids(user.username)

    user_json['properties'].update(
        {
            'edx_enrollments': enrollment_titles,
            'edx_enrollments_short_ids': enrollment_short_ids
        }
    )

    return user_json
