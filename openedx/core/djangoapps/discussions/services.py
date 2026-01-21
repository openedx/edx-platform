"""
Discussion Configuration Service for XBlock runtime.

This service provides discussion-related configuration and feature flags
that are specific to the edx-platform implementation
for the extracted discussion block in xblocks-contrib repository.
"""

from edx_django_utils.cache import DEFAULT_REQUEST_CACHE
from opaque_keys.edx.keys import CourseKey

from django.conf import settings
from openedx.core.djangoapps.django_comment_common.models import (
    all_permissions_for_user_in_course
)
from openedx.core.djangoapps.discussions.models import DiscussionsConfiguration, Provider


class DiscussionConfigService:
    """
    Service for providing video-related configuration and feature flags.
    """

    def discussion_permission(self, user, permission, course_id=None):  # lint-amnesty, pylint: disable=missing-function-docstring
        assert isinstance(course_id, (type(None), CourseKey))
        request_cache_dict = DEFAULT_REQUEST_CACHE.data
        cache_key = "django_comment_client.permissions.has_permission.all_permissions.{}.{}".format(
            user.id, course_id
        )
        if cache_key in request_cache_dict:
            all_permissions = request_cache_dict[cache_key]
        else:
            all_permissions = all_permissions_for_user_in_course(user, course_id)
            request_cache_dict[cache_key] = all_permissions

        return permission in all_permissions

    def is_discussion_visible(self, course_key):
        """
        Discussion Xblock does not support new OPEN_EDX provider
        """
        provider = DiscussionsConfiguration.get(course_key)
        return provider.provider_type == Provider.LEGACY

    def is_discussion_enabled(self):
        """
        Return True if discussions are enabled; else False
        """
        return settings.FEATURES.get('ENABLE_DISCUSSION_SERVICE')
