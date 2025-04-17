"""
Definition of "Library" as a learning context.
"""
import logging

from django.core.exceptions import PermissionDenied
from rest_framework.exceptions import NotFound

from openedx_events.content_authoring.data import LibraryBlockData, LibraryContainerData
from openedx_events.content_authoring.signals import LIBRARY_BLOCK_UPDATED, LIBRARY_CONTAINER_UPDATED
from opaque_keys.edx.keys import UsageKeyV2, OpaqueKey
from opaque_keys.edx.locator import LibraryContainerLocator, LibraryLocatorV2, LibraryUsageLocatorV2
from openedx_learning.api import authoring as authoring_api

from openedx.core.djangoapps.content_libraries import api, permissions
from openedx.core.djangoapps.content_libraries.models import ContentLibrary
from openedx.core.djangoapps.xblock.api import LearningContext
from openedx.core.types import User as UserType

log = logging.getLogger(__name__)


class LibraryContextPermissionBase:
    locator_type = OpaqueKey

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.use_draft = kwargs.get('use_draft', None)

    def get_library_key(self, opaque_key: OpaqueKey):
        """
        Get library key from given opaque_key.
        """
        raise NotImplementedError()

    def can_edit_block(self, user: UserType, opaque_key: OpaqueKey) -> bool:
        """
        Assuming a block with the specified ID (opaque_key) exists, does the
        specified user have permission to edit it (make changes to the
        fields / authored data store)?

        May raise ContentLibraryNotFound if the library does not exist.
        """
        assert isinstance(opaque_key, self.locator_type)
        return self._check_perm(
            user,
            self.get_library_key(opaque_key),
            permissions.CAN_EDIT_THIS_CONTENT_LIBRARY
        )

    def can_view_block_for_editing(self, user: UserType, opaque_key: OpaqueKey) -> bool:
        """
        Assuming a block with the specified ID (opaque_key) exists, does the
        specified user have permission to view its fields and OLX details (but
        not necessarily to make changes to it)?

        May raise ContentLibraryNotFound if the library does not exist.
        """
        assert isinstance(opaque_key, self.locator_type)
        return self._check_perm(
            user,
            self.get_library_key(opaque_key),
            permissions.CAN_VIEW_THIS_CONTENT_LIBRARY
        )

    def can_view_block(self, user: UserType, opaque_key: OpaqueKey) -> bool:
        """
        Does the specified usage key exist in its context, and if so, does the
        specified user have permission to view it and interact with it (call
        handlers, save user state, etc.)?

        May raise ContentLibraryNotFound if the library does not exist.
        """
        assert isinstance(opaque_key, self.locator_type)
        return self._check_perm(
            user,
            self.get_library_key(opaque_key),
            permissions.CAN_LEARN_FROM_THIS_CONTENT_LIBRARY
        )

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


class LibraryContextImpl(LibraryContextPermissionBase, LearningContext):
    """
    Implements content libraries as a learning context.

    This is the *new* content libraries based on Learning Core, not the old content
    libraries based on modulestore.
    """

    locator_type = LibraryUsageLocatorV2

    def get_library_key(self, opaque_key: OpaqueKey):
        """
        Get library key from given opaque_key.
        """
        return opaque_key.lib_key

    def block_exists(self, usage_key: LibraryUsageLocatorV2):
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
            content_lib = ContentLibrary.objects.get_by_key(usage_key.context_key)  # type: ignore[attr-defined]
        except ContentLibrary.DoesNotExist:
            return False

        learning_package = content_lib.learning_package
        if learning_package is None:
            return False

        return authoring_api.component_exists_by_key(
            learning_package.id,
            namespace='xblock.v1',
            type_name=usage_key.block_type,
            local_key=usage_key.block_id,
        )

    def send_block_updated_event(self, opaque_key: OpaqueKey):
        """
        Send a "block updated" event for the library block with the given usage_key.
        """
        assert isinstance(opaque_key, self.locator_type)
        LIBRARY_BLOCK_UPDATED.send_event(
            library_block=LibraryBlockData(
                library_key=opaque_key.lib_key,
                usage_key=opaque_key,
            )
        )

    def send_container_updated_events(self, opaque_key: OpaqueKey):
        """
        Send "container updated" events for containers that contains the library block
        with the given usage_key.
        """
        assert isinstance(opaque_key, self.locator_type)
        affected_containers = api.get_containers_contains_component(opaque_key)
        for container in affected_containers:
            LIBRARY_CONTAINER_UPDATED.send_event(
                library_container=LibraryContainerData(
                    container_key=container.container_key,
                    background=True,
                )
            )


class LibraryContextContainerImpl(LibraryContextPermissionBase, LearningContext):
    """
    Implements content libraries as a learning context for containers in libraries.

    This is the *new* content libraries based on Learning Core, not the old content
    libraries based on modulestore.
    """

    locator_type = LibraryContainerLocator

    def get_library_key(self, opaque_key: OpaqueKey):
        """
        Get library key from given opaque_key.
        """
        return opaque_key.library_key

    def container_exists(self, container_key: LibraryContainerLocator):
        """
        Does the container for this key exist in this Library?

        Note that this applies to all versions, i.e. you can put a container key for
        a piece of content that has been soft-deleted (removed from Drafts), and
        it will still return True here. That's because for the purposes of
        permission checking, we just want to know whether that block has ever
        existed in this Library, because we could be looking at any older
        version of it.
        """
        try:
            content_lib = ContentLibrary.objects.get_by_key(container_key.library_key)  # type: ignore[attr-defined]
        except ContentLibrary.DoesNotExist:
            return False

        learning_package = content_lib.learning_package
        if learning_package is None:
            return False

        return authoring_api.container_exists_by_key(
            learning_package.id,
            container_key,
        )

    def send_block_updated_event(self, opaque_key: OpaqueKey):
        """
        Send a "block updated" event for the library block with the given usage_key.
        """
        assert isinstance(opaque_key, self.locator_type)
        LIBRARY_CONTAINER_UPDATED.send_event(
            library_container=LibraryContainerData(
                container_key=opaque_key,
            )
        )
