"""
Event-tracking additions for Tahoe customer-specific metadata.

Custom event-tracking Processor to add properties to events.
"""

from json.decoder import JSONDecodeError
import logging

from celery import task
from crum import get_current_user
from django.core.cache import cache

from . import app_variant


logger = logging.getLogger(__name__)


class TahoeUserProfileMetadataCache(object):
    """Cache metadata from UserProfile."""

    # TODO: rework as a singleton.

    CACHE_KEY_PREFIX = "appsembler_eventtracking_user_metadata_by_user_id"
    READY = False
    PREFILLING = False

    def _make_key_by_user_id(self, user_id):
        return '{}-{}'.format(self.CACHE_KEY_PREFIX, user_id)

    def get_by_user_id(self, user_id):
        if not self.READY:
            return None
        return cache.get(self._make_key_by_user_id(user_id))

    def set_by_user_id(self, user_id, val):
        if not self.READY:
            return None
        key = self._make_key_by_user_id(user_id)
        cache.set(key, val)
        logger.debug('Set and retrieved {} with value {}'.format(key, cache.get(key)))

    def invalidate(self, instance):
        # called by signal handler on post_save, post_delete of UserProfile
        key = self._make_key_by_user_id(instance.user_id)
        if not self.READY:
            logger.info('Tried to delete {} before cache was done prefetching'.format(key))
            return
        cache.delete(key)


@task(routing_key=settings.PREFETCH_TAHOE_USERMETADATA_CACHE_QUEUE, bind=True)
def prefetch_tahoe_usermetadata_cache(self, cache_instance):
    """Celery task to prefetch UserProfile metadata for all users."""
    cache_instance.PREFILLING = True

    logger.info("START Prefilling Tahoe UserMetadata Cache...")

    from student.models import UserProfile

    for up in UserProfile.objects.all().select_related('user'):
        cache_instance.set_by_user_id(up.user.id, up.get_meta().get('tahoe_idp_metadata', {}))

    cache_instance.PREFILLING = False
    cache_instance.READY = True
    logger.info("FINISH Prefilling Tahoe UserMetadata Cache")

    return True  # TODO: not sure what we want to return here for the task_success signal


class TahoeUserMetadataProcessor(object):
    """
    Event tracking Processor for Tahoe User Data.

    Always returns the event for continued processing.
    """

    def _get_reg_metadata_from_cache(self, user_id):
        cached = userprofile_metadata_cache.get_by_user_id(user_id)
        if cached:
            return cached
        else:
            return {}

    def _get_custom_registration_metadata(self, user_id):
        """
        Get any custom registration field data for the User.

        Retrieved from the `registration_additional` property of `tahoe_idp_metadata`.
        Returns a dictionary.
        """
        # look in cache first
        cached_metadata = self._get_reg_metadata_from_cache(user_id)
        reg_additional = cached_metadata.get('registration_additional')
        if reg_additional:
            return reg_additional

        # local import, as module is loaded at startup via eventtracking.django for Processor init
        from student.models import UserProfile
        try:
            profile = UserProfile.objects.get(user__id=user_id)
        except UserProfile.DoesNotExist:
            logger.info("User {user_id} has no UserProfile".format(user_id=user_id))
            return {}
        meta = profile.get_meta()
        idp_metadata = meta.get("tahoe_idp_metadata", {})
        custom_reg_data = idp_metadata.get("registration_additional")
        userprofile_metadata_cache.set_by_user_id(user_id, idp_metadata)
        return custom_reg_data

    def _get_user_tahoe_metadata(self, user_id):
        """Build additional tracking context from Tahoe IDP metadata about the user."""
        # for now we only get custom registration field values
        try:
            custom_reg_data = self._get_custom_registration_metadata(user_id)
        except JSONDecodeError:
            logger.info("Bad JSON in UserProfile.meta for user id {}".format(user_id))
            return {"ERROR": "Bad JSON in User's metadata"}

        return {"registration_extra": custom_reg_data}

        # there may eventually be others we want to add as event context

    def __call__(self, event):
        """Process the event and return the event."""
        # WARNING:
        # We have to be careful to not add SQL queries that would require updating upstream tests
        # which count SQL queries; e.g., `cms.djangoapps.contentstore.views.tests.test_course_index)
        # currently we can do this by only enabling the event processor for LMS
        if app_variant.is_not_lms():  # we don't care about user metadata for Studio, at this point
            return event

        user = get_current_user()
        if not user or not user.pk:
            # should be an AnonymousUser or in tests
            return event

        # Add any Tahoe metadata context
        tahoe_user_metadata = self._get_user_tahoe_metadata(user.pk)
        if tahoe_user_metadata:
            event['context']['tahoe_user_metadata'] = tahoe_user_metadata

        return event


userprofile_metadata_cache = TahoeUserProfileMetadataCache()
