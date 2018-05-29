from celery import task
from lms.djangoapps.onboarding.models import (UserExtendedProfile, Organization, FocusArea, OrgSector)
from mailchimp_pipeline.client import ChimpClient, MailChimpException
from logging import getLogger
log = getLogger(__name__)


@task()
def update_org_details_at_mailchimp(org_name, list_id):
    log.info("Task to send  organization details to Mailchimp")
    log.info(org_name)
    organization = Organization.objects.filter(label__iexact=org_name.lower()).first()
    extended_profiles = UserExtendedProfile.objects.filter(organization=organization).values("user__email")
    focus_areas = FocusArea.get_map()
    org_sectors = OrgSector.get_map()

    for extended_profile in extended_profiles:
        org_type = ""
        if organization.org_type:
            org_type = org_sectors.get(organization.org_type, "")

        user_json = {
            "merge_fields": {
                "ORG": organization.label,
                "ORGTYPE": org_type,
                "WORKAREA": str(focus_areas.get(organization.focus_area, "")) if organization else "",
            }
        }
        try:
            response = ChimpClient().add_update_member_to_list(list_id, extended_profile.get('user__email'), user_json)
            log.info(response)
        except MailChimpException as ex:
            log.exception(ex)
