"""
Appsembler-specific event-tracking contexts.

Call these via middleware or an event-tracking Processor to add custom context to events.

TODO: Consider whether we should use `openedx.core.djangoapps.user_api.models.UserOrgTag`
to store these instead of UserProfile.meta.  There is an existing UserCourseTagContext middleware
that does a similar thing to here.
"""

import logging

from student.models import UserProfile

logger = logging.getLogger(__name__)


def _add_custom_registration_metadata(user_id):
    """
    Get any custom registration field data for the User.

    Retrieved from the `registration_additional` property of `tahoe_idp_metadata`.
    Returns a dictionary.
    """
    try:
        # TODO: retrieve from cache first, if available
        profile = UserProfile.objects.get(user__id=user_id)
        idp_metadata = profile.meta.get("tahoe_idp_metadata", {})
        custom_reg_data = idp_metadata.get("registration_additional")
        return custom_reg_data
    except UserProfile.DoesNotExist:
        logger.info("User {user_id} has no UserProfile".format(user_id=user_id))
        return {}


def user_tahoe_idp_metadata_context(user_id):
    """Build additional tracking context from Tahoe IDP metadata about the user."""
    # for now we only get custom registration field values

    return _add_custom_registration_metadata(user_id)
