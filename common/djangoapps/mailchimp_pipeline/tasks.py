from celery import task
from lms.djangoapps.onboarding.models import UserExtendedProfile
from mailchimp_pipeline.client import ChimpClient, MailChimpException
from logging import getLogger
log = getLogger(__name__)


@task()
def update_org_details_at_mailchimp(org_label, org_type, work_area, list_id):
    log.info("Task to send organization details to MailChimp")
    log.info(org_label)

    extended_profiles = UserExtendedProfile.objects.filter(organization__label__iexact=org_label.lower()).values("user__email")

    for extended_profile in extended_profiles:
        user_json = {
            "merge_fields": {
                "ORG": org_label,
                "ORGTYPE": org_type,
                "WORKAREA": work_area
            }
        }
        try:
            response = ChimpClient().add_update_member_to_list(list_id, extended_profile.get('user__email'), user_json)
            log.info(response)
        except MailChimpException as ex:
            log.exception(ex)
