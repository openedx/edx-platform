"""
Definition of "Library" as a learning context.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import logging

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
        super(LibraryContextImpl, self).__init__(**kwargs)
        self.use_draft = kwargs.get('use_draft', None)

    def can_edit_block(self, user, usage_key):
        """
        Does the specified usage key exist in its context, and if so, does the
        specified user (which may be an AnonymousUser) have permission to edit
        it?

        Must return a boolean.
        """
        def_key = self.definition_for_usage(usage_key)
        if not def_key:
            return False
        # TODO: implement permissions
        return True

    def can_view_block(self, user, usage_key):
        """
        Does the specified usage key exist in its context, and if so, does the
        specified user (which may be an AnonymousUser) have permission to view
        it and interact with it (call handlers, save user state, etc.)?

        Must return a boolean.
        """
        def_key = self.definition_for_usage(usage_key)
        if not def_key:
            return False
        # TODO: implement permissions
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
        if 'force_draft' in kwargs:
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
