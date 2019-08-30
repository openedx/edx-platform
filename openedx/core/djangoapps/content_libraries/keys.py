"""
Key/locator types for Blockstore-based content libraries
"""
# Disable warnings about _to_deprecated_string etc. which we don't want to implement:
# pylint: disable=abstract-method, no-member
from __future__ import absolute_import, division, print_function, unicode_literals

from opaque_keys import InvalidKeyError

from openedx.core.djangoapps.xblock.learning_context.keys import (
    check_key_string_field,
    BlockUsageKeyV2,
    LearningContextKey,
)


class LibraryLocatorV2(LearningContextKey):
    """
    A key that represents a Blockstore-based content library.

    When serialized, these keys look like:
        lib:MITx:reallyhardproblems
        lib:hogwarts:p300-potions-exercises
    """
    CANONICAL_NAMESPACE = 'lib'
    KEY_FIELDS = ('org', 'slug')
    __slots__ = KEY_FIELDS
    CHECKED_INIT = False

    def __init__(self, org, slug):
        """
        Construct a GlobalUsageLocator
        """
        check_key_string_field(org)
        check_key_string_field(slug)
        super(LibraryLocatorV2, self).__init__(org=org, slug=slug)

    def _to_string(self):
        """
        Serialize this key as a string
        """
        return ":".join((self.org, self.slug))

    @classmethod
    def _from_string(cls, serialized):
        """
        Instantiate this key from a serialized string
        """
        try:
            (org, slug) = serialized.split(':')
        except ValueError:
            raise InvalidKeyError(cls, serialized)
        return cls(org=org, slug=slug)

    def make_definition_usage(self, definition_key, usage_id=None):
        """
        Return a usage key, given the given the specified definition key and
        usage_id.
        """
        return LibraryUsageLocatorV2(
            library_org=self.org,
            library_slug=self.slug,
            block_type=definition_key.block_type,
            usage_id=usage_id,
        )

    def for_branch(self, branch):
        """
        Compatibility helper.
        Some code calls .for_branch(None) on course keys. By implementing this,
        it improves backwards compatibility between library keys and course
        keys.
        """
        if branch is not None:
            raise ValueError("Cannot call for_branch on a content library key, except for_branch(None).")
        return self


class LibraryUsageLocatorV2(BlockUsageKeyV2):
    """
    An XBlock in a Blockstore-based content library.

    When serialized, these keys look like:
        lb:MITx:reallyhardproblems:problem:problem1
    """
    CANONICAL_NAMESPACE = 'lb'  # "Library Block"
    KEY_FIELDS = ('library_org', 'library_slug', 'block_type', 'usage_id')
    __slots__ = KEY_FIELDS
    CHECKED_INIT = False

    def __init__(self, library_org, library_slug, block_type, usage_id):
        """
        Construct a LibraryUsageLocatorV2
        """
        check_key_string_field(library_org)
        check_key_string_field(library_slug)
        check_key_string_field(block_type)
        check_key_string_field(usage_id)
        super(LibraryUsageLocatorV2, self).__init__(
            library_org=library_org,
            library_slug=library_slug,
            block_type=block_type,
            usage_id=usage_id,
        )

    @property
    def context_key(self):
        return LibraryLocatorV2(org=self.library_org, slug=self.library_slug)

    @property
    def block_id(self):
        """
        Get the 'block ID' which is another name for the usage ID.
        """
        return self.usage_id

    def _to_string(self):
        """
        Serialize this key as a string
        """
        return ":".join((self.library_org, self.library_slug, self.block_type, self.usage_id))

    @classmethod
    def _from_string(cls, serialized):
        """
        Instantiate this key from a serialized string
        """
        try:
            (library_org, library_slug, block_type, usage_id) = serialized.split(':')
        except ValueError:
            raise InvalidKeyError(cls, serialized)
        return cls(library_org=library_org, library_slug=library_slug, block_type=block_type, usage_id=usage_id)
