"""
Discussion Configuration Service for XBlock runtime.

This service provides discussion-related configuration and feature flags
that are specific to the edx-platform implementation
for the extracted discussion block in xblocks-contrib repository.
"""

from django.conf import settings
from lms.djangoapps.discussion.django_comment_client.permissions import has_permission
from openedx.core.djangoapps.discussions.models import DiscussionsConfiguration, Provider


class DiscussionConfigService:

    def discussion_permission(self, user, permission, course_id=None):  # lint-amnesty, pylint: disable=missing-function-docstring
        return has_permission(user, permission, course_id)

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
