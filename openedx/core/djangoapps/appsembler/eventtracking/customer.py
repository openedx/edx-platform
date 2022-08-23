"""
Event-tracking additions for Tahoe customer-specific metadata.

Custom event-tracking Processor to add properties to events.
"""

import logging

from student.models import UserProfile


logger = logging.getLogger(__name__)


class UserTahoeIdpMetadataProcessor(object):
    """
    Add Tahoe IDP (Identity Provider) metadata for user to event.

    Retrieve metadata as stored on UserProfile.
    """

    def _add_custom_registration_fields(self, event):
        """Add custom registration properties and values to the event.

        Retrieved from the `registration_additional` property of `tahoe_idp_metadata`.
        Returns the modified event.
        """
        try:
            user_id = event["context"]["user_id"]
        except KeyError:
            logger.debug("Found no user_id in event['context']")
            return event

        try:
            profile = UserProfile.objects.get(user__id=user_id)
            idp_metadata = profile.meta.get("tahoe_idp_metadata", {})
            custom_reg_data = idp_metadata.get("registration_additional")
            event["context"]["user_registration_extra"] = custom_reg_data
        except UserProfile.DoesNotExist:
            logger.debug("User {user_id} has no UserProfile".format(user_id=user_id))

        return event

    def __call__(self, event):
        """Process and return the event for continued processing."""
        event = self._add_custom_registration_fields(event)
        return event
