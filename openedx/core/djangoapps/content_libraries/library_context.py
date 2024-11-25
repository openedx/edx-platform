"""
Definition of "Library" as a learning context.
"""
<<<<<<< HEAD

import logging

from django.core.exceptions import PermissionDenied
=======
import logging

from django.core.exceptions import PermissionDenied
from rest_framework.exceptions import NotFound

from openedx_events.content_authoring.data import LibraryBlockData
from openedx_events.content_authoring.signals import LIBRARY_BLOCK_UPDATED
from opaque_keys.edx.keys import UsageKeyV2
from opaque_keys.edx.locator import LibraryUsageLocatorV2, LibraryLocatorV2
from openedx_learning.api import authoring as authoring_api
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

from openedx.core.djangoapps.content_libraries import api, permissions
from openedx.core.djangoapps.content_libraries.models import ContentLibrary
from openedx.core.djangoapps.xblock.api import LearningContext
<<<<<<< HEAD

from openedx_learning.core.components import api as components_api
=======
from openedx.core.types import User as UserType
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

log = logging.getLogger(__name__)


class LibraryContextImpl(LearningContext):
    """
    Implements content libraries as a learning context.

<<<<<<< HEAD
    This is the *new* content libraries based on Blockstore, not the old content
=======
    This is the *new* content libraries based on Learning Core, not the old content
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    libraries based on modulestore.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.use_draft = kwargs.get('use_draft', None)

<<<<<<< HEAD
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
=======
    def can_edit_block(self, user: UserType, usage_key: UsageKeyV2) -> bool:
        """
        Assuming a block with the specified ID (usage_key) exists, does the
        specified user have permission to edit it (make changes to the
        fields / authored data store)?

        May raise ContentLibraryNotFound if the library does not exist.
        """
        assert isinstance(usage_key, LibraryUsageLocatorV2)
        return self._check_perm(user, usage_key.lib_key, permissions.CAN_EDIT_THIS_CONTENT_LIBRARY)

    def can_view_block_for_editing(self, user: UserType, usage_key: UsageKeyV2) -> bool:
        """
        Assuming a block with the specified ID (usage_key) exists, does the
        specified user have permission to view its fields and OLX details (but
        not necessarily to make changes to it)?

        May raise ContentLibraryNotFound if the library does not exist.
        """
        assert isinstance(usage_key, LibraryUsageLocatorV2)
        return self._check_perm(user, usage_key.lib_key, permissions.CAN_VIEW_THIS_CONTENT_LIBRARY)

    def can_view_block(self, user: UserType, usage_key: UsageKeyV2) -> bool:
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        """
        Does the specified usage key exist in its context, and if so, does the
        specified user have permission to view it and interact with it (call
        handlers, save user state, etc.)?

<<<<<<< HEAD
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
=======
        May raise ContentLibraryNotFound if the library does not exist.
        """
        assert isinstance(usage_key, LibraryUsageLocatorV2)
        return self._check_perm(user, usage_key.lib_key, permissions.CAN_LEARN_FROM_THIS_CONTENT_LIBRARY)

    def _check_perm(self, user: UserType, lib_key: LibraryLocatorV2, perm) -> bool:
        """ Helper method to check a permission for the various can_ methods"""
        try:
            api.require_permission_for_library_key(lib_key, user, perm)
            return True
        except PermissionDenied:
            return False
        except api.ContentLibraryNotFound as exc:
            # A 404 is probably what you want in this case, not a 500 error, so do that by default.
            raise NotFound(f"Content Library '{lib_key}' does not exist") from exc

    def block_exists(self, usage_key: LibraryUsageLocatorV2):
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
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
<<<<<<< HEAD
            content_lib = ContentLibrary.objects.get_by_key(usage_key.context_key)
=======
            content_lib = ContentLibrary.objects.get_by_key(usage_key.context_key)  # type: ignore[attr-defined]
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        except ContentLibrary.DoesNotExist:
            return False

        learning_package = content_lib.learning_package
        if learning_package is None:
            return False

<<<<<<< HEAD
        return components_api.component_exists_by_key(
=======
        return authoring_api.component_exists_by_key(
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
            learning_package.id,
            namespace='xblock.v1',
            type_name=usage_key.block_type,
            local_key=usage_key.block_id,
        )
<<<<<<< HEAD
=======

    def send_block_updated_event(self, usage_key: UsageKeyV2):
        """
        Send a "block updated" event for the library block with the given usage_key.
        """
        assert isinstance(usage_key, LibraryUsageLocatorV2)
        LIBRARY_BLOCK_UPDATED.send_event(
            library_block=LibraryBlockData(
                library_key=usage_key.lib_key,
                usage_key=usage_key,
            )
        )
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
