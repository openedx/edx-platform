import base64
from uuid import UUID

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import DefinitionKey


class BundleDefinitionLocator(DefinitionKey):
    """
    Implementation of the DefinitionKey type, for XBlock content stored in
    Blockstore bundles (.olx files).

    Each BundleDefinitionLocator holds the following data
        bundle UUID (e.g. fc4d4d8d-60b3-4aad-b9f1-4ea738505d13)
        OLX file path (e.g. /unit-welcome/welcome.olx)
        Block type (of some block within the OLX file, e.g. 'html')
        Block definition ID (of some block within the OLX file, e.g. 'intro')
    
    Note that we do not store bundle slugs (rather UUIDs), because the slugs
    may change. These definition keys are more for internal use than for
    displaying to users.
    """
    CANONICAL_NAMESPACE = 'olx-v1'
    KEY_FIELDS = ('bundle_uuid', 'olx_path', 'block_type', 'definition_id')
    __slots__ = KEY_FIELDS
    CHECKED_INIT = False

    def __init__(self, bundle_uuid, olx_path, block_type, definition_id):
        if not isinstance(bundle_uuid, UUID):
            bundle_uuid = UUID(bundle_uuid)
        if len(olx_path) < 2 or olx_path[0] != '/' or olx_path.find(':') != -1:
            raise InvalidKeyError("Invalid OLX path.")
        super(BundleDefinitionLocator, self).__init__(
            bundle_uuid=bundle_uuid,
            olx_path=olx_path,
            block_type=block_type,
            definition_id=definition_id,
        )

    @classmethod
    def _olx_path_shortened(cls, olx_path):
        """
        Convert an arbitrary OLX path to a potentially shorter format.
        The result is shorter if the olx path is in the standard format
        /block_type-block_id/block_id.olx

        The result is a string like "block_type/block_id" or the original string.

        Returns a tuple: short_string, type_part or None, id_part or None
        """
        if len(olx_path) < 2 or olx_path[0] != '/':
            raise InvalidKeyError("An OLX path must start with / and contain a filename")
        if olx_path.endswith('.olx'):
            id_part = olx_path[:-4].rpartition('/')[2]  # from "/foo/bar.olx", get "bar"
            type_part = olx_path[1:].partition('-' + id_part + '/')[0] # from "/foo-bar/bar.olx", get "foo"
            short_path = type_part + '/' + id_part
            if cls._olx_path_expanded(short_path)[0] == olx_path:
                return (short_path, type_part, id_part)
        return (olx_path, None, None)

    @classmethod
    def _olx_path_expanded(cls, olx_path_shortened):
        """
        Convert a potentially shortened OLX path to the full expanded form
        The result is a string like "/block_type-block_id/block_id.olx"

        Returns a tuple: olx_path, type_part or None, id_part or None
        """
        if len(olx_path_shortened) < 2:
            raise InvalidKeyError("Invalid short OLX path")
        if olx_path_shortened[0] == '/':
            return (olx_path_shortened, None, None)  # It's a normal OLX path
        try:
            type_part, _, id_part = olx_path_shortened.partition('/')
        except ValueError:
            raise InvalidKeyError("Invalid short OLX path")
        olx_path = '/' + type_part + '-' + id_part + '/' + id_part + '.olx'
        return (olx_path, type_part, id_part)

    @staticmethod
    def _b64_encode(data):
        """ Encode arbitrary bytes in a URL-friendly base64 format """
        return base64.b64encode(data, '-_').rstrip('=')

    @staticmethod
    def _b64_decode(encoded):
        """ Inverse of _b64_encode """
        encoded = encoded + '=' * (3 - len(encoded) % 3)  # Fix padding
        if isinstance(encoded, unicode):
            encoded = encoded.encode('utf8')
        return base64.b64decode(encoded, '-_')

    def _to_string(self):
        """
        Return a string representing this location in blockstore.

        The encoding is a bit complex in order to keep the string length down.
        """
        bundle_uuid_encoded = self._b64_encode(self.bundle_uuid.bytes)
        olx_path_encoded, root_type, root_id = self._olx_path_shortened(self.olx_path)
        block_type_encoded = '' if self.block_type == root_type else self.block_type
        definition_id_encoded = '' if self.definition_id == root_id else self.definition_id

        return u":".join((
            bundle_uuid_encoded,
            olx_path_encoded,
            block_type_encoded,
            definition_id_encoded,
        ))

    @classmethod
    def _from_string(cls, serialized):
        """
        Return a DefinitionLocator parsing the given serialized string
        :param serialized: matches the string to
        """
        try:
            (
                bundle_uuid_encoded,
                olx_path_encoded,
                block_type_encoded,
                definition_id_encoded,
            ) = serialized.split(':')
        except ValueError:
            raise InvalidKeyError("Not a valid bundle definition")

        bundle_uuid = UUID(bytes=cls._b64_decode(bundle_uuid_encoded))
        olx_path, root_type, root_id = cls._olx_path_expanded(olx_path_encoded)
        block_type = block_type_encoded if block_type_encoded else root_type
        definition_id = definition_id_encoded if definition_id_encoded else root_id
        if not block_type or not definition_id:
            raise InvalidKeyError("Not a valid bundle definition")

        return cls(
            bundle_uuid=bundle_uuid,
            olx_path=olx_path,
            block_type=block_type,
            definition_id=definition_id,
        )
