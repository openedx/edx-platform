"""
Definition of "Library" as a learning context.
"""

import logging

from django.core.exceptions import PermissionDenied

from openedx.core.djangoapps.content_libraries import api, permissions
from openedx.core.djangoapps.content_libraries.library_bundle import (
    LibraryBundle,
    bundle_uuid_for_library_key,
    usage_for_child_include,
)
from openedx.core.djangoapps.content_libraries.models import ContentLibrary
from openedx.core.djangoapps.xblock.learning_context import LearningContext

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
        def_key = self.definition_for_usage(usage_key)
        if not def_key:
            return False
        return True

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
        def_key = self.definition_for_usage(usage_key)
        if not def_key:
            return False
        return True

    def definition_for_usage(self, usage_key, **kwargs):
        """
        Given a usage key for an XBlock in this context, return the
        BundleDefinitionLocator which specifies the actual XBlock definition
        (as a path to an OLX in a specific blockstore bundle).

        Must return a BundleDefinitionLocator if the XBlock exists in this
        context, or None otherwise.
        """
        library_key = usage_key.context_key
        try:
            bundle_uuid = bundle_uuid_for_library_key(library_key)
        except ContentLibrary.DoesNotExist:
            return None
        if 'force_draft' in kwargs:  # lint-amnesty, pylint: disable=consider-using-get
            use_draft = kwargs['force_draft']
        else:
            use_draft = self.use_draft
        bundle = LibraryBundle(library_key, bundle_uuid, use_draft)
        return bundle.definition_for_usage(usage_key)

    def usage_for_child_include(self, parent_usage, parent_definition, parsed_include):
        """
        Method that the runtime uses when loading a block's child, to get the
        ID of the child.

        The child is always from an <xblock-include /> element.
        """
        return usage_for_child_include(parent_usage, parent_definition, parsed_include)
