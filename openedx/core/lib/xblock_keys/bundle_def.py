"""
Implementation of keys to locate XBlock definitions in Blockstore
"""
# Disable warnings about _to_deprecated_string etc. which we don't want to implement.
# And fix warnings about key fields, which pylint doesn't see as member variables.
# pylint: disable=abstract-method, no-member
from __future__ import absolute_import, division, print_function, unicode_literals
from uuid import UUID

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import DefinitionKey
import six


class BundleDefinitionLocator(DefinitionKey):
    """
    Implementation of the DefinitionKey type, for XBlock content stored in
    Blockstore bundles (.olx files).

    Each BundleDefinitionLocator holds the following data
        bundle UUID (e.g. fc4d4d8d-60b3-4aad-b9f1-4ea738505d13)
        Block type (of some block within an OLX file in the bundle, e.g. 'html')
        Block definition ID (url_name value of some block within the OLX file, e.g. 'intro')
    """
    CANONICAL_NAMESPACE = 'olx-v1'
    KEY_FIELDS = ('bundle_uuid', 'block_type', 'definition_id')
    __slots__ = KEY_FIELDS
    CHECKED_INIT = False

    def __init__(self, bundle_uuid, block_type, definition_id):
        if not isinstance(bundle_uuid, UUID):
            bundle_uuid = UUID(bundle_uuid)
        assert block_type and isinstance(block_type, six.string_types)
        assert definition_id and isinstance(definition_id, six.string_types)
        super(BundleDefinitionLocator, self).__init__(
            bundle_uuid=bundle_uuid,
            block_type=block_type,
            definition_id=definition_id,
        )

    def _to_string(self):
        """
        Return a string representing this location in blockstore.
        """
        return ":".join((
            six.text_type(self.bundle_uuid),
            self.block_type,
            self.definition_id,
        ))

    @classmethod
    def _from_string(cls, serialized):
        """
        Return a BundleDefinitionLocator by parsing the given serialized string
        """
        try:
            (
                bundle_uuid_str,
                block_type,
                definition_id,
            ) = serialized.split(':', 2)
        except ValueError:
            raise InvalidKeyError(cls, serialized)

        bundle_uuid = UUID(bundle_uuid_str)
        if not block_type or not definition_id:
            raise InvalidKeyError(cls, serialized)

        return cls(
            bundle_uuid=bundle_uuid,
            block_type=block_type,
            definition_id=definition_id,
        )
