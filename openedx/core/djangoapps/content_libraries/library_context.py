"""
Definition of "Library" as a learning context.
"""

import logging

from django.core.exceptions import PermissionDenied

from openedx.core.djangoapps.content_libraries import api, permissions
from openedx.core.djangoapps.content_libraries.models import ContentLibrary
from openedx.core.djangoapps.xblock.api import LearningContext

from openedx_learning.core.components import api as components_api

log = logging.getLogger(__name__)


class LibraryContextImpl(LearningContext):
    """
    Implements content libraries as a learning context.

    This is the *new* content libraries based on Blockstore, not the old content
    libraries based on modulestore.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.use_draft = kwargs.get('use_draft', None)

    def can_edit_block(self, user, usage_key):
        """
        Does the specified usage key exist in its context, and if so, does the
        specified user have permission to edit it (make changes to the authored
        data store)?

        user: a Django User object (may be an AnonymousUser)

        usage_key: the UsageKeyV2 subclass used for this learning context

        Must return a boolean.
        """
        try:
            api.require_permission_for_library_key(usage_key.lib_key, user, permissions.CAN_EDIT_THIS_CONTENT_LIBRARY)
        except (PermissionDenied, api.ContentLibraryNotFound):
            return False

        return self.block_exists(usage_key)

    def can_view_block(self, user, usage_key):
        """
        Does the specified usage key exist in its context, and if so, does the
        specified user have permission to view it and interact with it (call
        handlers, save user state, etc.)?

        user: a Django User object (may be an AnonymousUser)

        usage_key: the UsageKeyV2 subclass used for this learning context

        Must return a boolean.
        """
        try:
            api.require_permission_for_library_key(
                usage_key.lib_key, user, permissions.CAN_LEARN_FROM_THIS_CONTENT_LIBRARY,
            )
        except (PermissionDenied, api.ContentLibraryNotFound):
            return False

        return self.block_exists(usage_key)

    def block_exists(self, usage_key):
        """
        Does the block for this usage_key exist in this Library?

        Note that this applies to all versions, i.e. you can put a usage key for
        a piece of content that has been soft-deleted (removed from Drafts), and
        it will still return True here. That's because for the purposes of
        permission checking, we just want to know whether that block has ever
        existed in this Library, because we could be looking at any older
        version of it.
        """
        try:
            content_lib = ContentLibrary.objects.get_by_key(usage_key.context_key)
        except ContentLibrary.DoesNotExist:
            return False

        learning_package = content_lib.learning_package
        if learning_package is None:
            return False

        return components_api.component_exists_by_key(
            learning_package.id,
            namespace='xblock.v1',
            type_name=usage_key.block_type,
            local_key=usage_key.block_id,
        )
