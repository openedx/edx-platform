from mailchimp_pipeline.client import ChimpClient, MailChimpException
from mailchimp_pipeline.tasks import update_org_details_at_mailchimp
from lms.djangoapps.onboarding.models import (UserExtendedProfile, FocusArea, OrgSector, Organization,)
from student.models import UserProfile
from logging import getLogger
log = getLogger(__name__)

list_id = "885da93a66"


def send_user_profile_info_to_mailchimp(sender, instance, kwargs):  # pylint: disable=unused-argument, invalid-name
    """ Create user account at nodeBB when user created at edx Platform """
    user_json = None
    if sender == UserProfile:
        profile = instance
        user_json = {
            "merge_fields": {
                "LANG": profile.language if profile.language else "",
                "COUNTRY": profile.country.name.format() if profile.country else "",
                "CITY": profile.city if profile.city else "",
            }
        }
    elif sender == UserExtendedProfile:
        extended_profile = instance
        user_json = {
            "merge_fields": {
                "ORG": extended_profile.organization.label if extended_profile.organization else ""
            }
        }
    elif sender == Organization:
        update_org_details_at_mailchimp.delay(instance.label, list_id)

    if user_json and not sender == Organization:
        try:
            response = ChimpClient().add_update_member_to_list(list_id, instance.user.email, user_json)
            log.info(response)
        except MailChimpException as ex:
            log.exception(ex)


def send_user_info_to_mailchimp(sender, user, created, kwargs):
    """ Create user account at nodeBB when user created at edx Platform """

    user_json = {
        "merge_fields": {
            "FULLNAME": user.get_full_name(),
            "USERNAME": user.username,
        }
    }

    if created:
        user_json.update({
            "email_address": user.email,
            "status_if_new": "subscribed",
            "DATEJOINED": user.date_joined.strftime("%m/%d/%Y")
        })
    try:
        response = ChimpClient().add_update_member_to_list(list_id, user.email, user_json)
        log.info(response)
    except MailChimpException as ex:
        log.exception(ex)
