"""
Event-tracking additions for Tahoe customer-specific metadata.

Custom event-tracking Processor to add properties to events.
"""

from collections import defaultdict
import logging

from crum import get_current_user
from django.db.models.signals import post_save, post_delete

from openedx.core.lib import cache_utils


logger = logging.getLogger(__name__)


class TahoeUserProfileIdpMetadataCache(object):
    """Cache user Tahoe IDP Metadata from UserProfile."""

    # we want to initialize the cache at startup time but we can't do this
    # until appregistry is ready
    # we also don't want to do this in the ready() every time

    CACHE_NAMESPACE = "appsembler.eventtracking.userprofile.tahoe_idp_metadata"
    CACHE_KEY = "idp_metadata_by_user_id"

    def __init__(self):
        from student.models import UserProfile

        # we can do this in an AppConfig.ready
        post_save.connect(self.invalidate, sender=UserProfile)
        post_delete.connect(self.invalidate, sender=UserProfile)

    def prefetch(self):
        """Populate user tahoe_idp_metadata."""
        metadata_by_user_id = defaultdict(set)
        cache_utils.get_cache(self.CACHE_NAMESPACE)[self.CACHE_KEY] = metadata_by_user_id

        # for up in UserProfile.objects.all().select_related('user'):
        #     metadata_by_user_id[up.user.id].add(up.meta.get('tahoe_idp_metadata', {}))

    def get_by_user_id(self, user_id):
        return cache_utils.get_cache(self.CACHE_NAMESPACE)[self.CACHE_KEY][user_id]

    def set_by_user_id(self, user_id, val):
        cache_utils.get_cache(self.CACHE_NAMESPACE)[self.CACHE_KEY][user_id] = val

    def invalidate(self, sender, instance):
        del cache_utils.get_cache(self.CACHE_NAMESPACE)[self.CACHE_KEY][instance.id]


class TahoeUserMetadataProcessor(object):
    """
    Event tracking Processor for Tahoe User Data.

    Always returns the event for continued processing.
    """

    def __init__(self):
        # prefetch the tahoe_idp_metadata at instantiation to fill cache
        # self.cache = TahoeUserProfileIdpMetadataCache()
        # self.cache.prefetch()
        pass

    def _get_reg_metadata_from_cache(self, user_id):
        self.cache.get_by_user_id(user_id)

    def _get_custom_registration_metadata(self, user_id):
        """
        Get any custom registration field data for the User.

        Retrieved from the `registration_additional` property of `tahoe_idp_metadata`.
        Returns a dictionary.
        """
        # look in cache first
        # cached_reg_additional = self._get_reg_metadata_from_cache().get("registration_additional")
        # if cached_reg_additional:
        #     return cached_reg_additional

        # janky, but for now
        from student.models import UserProfile
        try:
            # TODO: retrieve from cache first, if available
            profile = UserProfile.objects.get(user__id=user_id)
            meta = profile.get_meta()
            idp_metadata = meta.get("tahoe_idp_metadata", {})
            custom_reg_data = idp_metadata.get("registration_additional")
            # self.cache.set_by_user_id(user_id, idp_metadata)
            return custom_reg_data
        except UserProfile.DoesNotExist:
            logger.info("User {user_id} has no UserProfile".format(user_id=user_id))
            return {}

    def _get_user_tahoe_metadata(self, user_id):
        """Build additional tracking context from Tahoe IDP metadata about the user."""
        # for now we only get custom registration field values

        return {"registration_extra": self._get_custom_registration_metadata(user_id)}

        # there may eventually be others we want to add as event context

    def __call__(self, event):
        """
        Process the event.

        If need be to handle cases without a request, we can check:
        os.environ.get('CELERY_WORKER_RUNNING', False))
        """
        user = get_current_user()
        if not user.pk:
            # should be an AnonymousUser
            return event

        # Add any Tahoe metadata context
        tahoe_user_metadata = self._get_user_tahoe_metadata(user.pk)
        if tahoe_user_metadata:
            event['context']['tahoe_user_metadata'] = tahoe_user_metadata

        return event
