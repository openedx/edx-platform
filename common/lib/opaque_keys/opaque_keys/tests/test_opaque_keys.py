from unittest import TestCase
from stevedore.extension import ExtensionManager, Extension
from mock import Mock

from opaque_keys import OpaqueKey, InvalidKeyError


def _mk_extension(name, cls):
    return Extension(
        name,
        Mock(name='entry_point_{}'.format(name)),
        cls,
        Mock(name='obj_{}'.format(name)),
    )


class DummyKey(OpaqueKey):
    """
    Key type for testing
    """
    KEY_TYPE = 'testing'

    def __init__(self, value):
        self._value = value

    @classmethod
    def drivers(cls):
        # Set up a fake extension manager for testing
        return ExtensionManager.make_test_instance(
            [
                _mk_extension('hex', HexKey),
                _mk_extension('base10', Base10Key),
            ]
        )


class HexKey(DummyKey):
    def _to_string(self):
        return hex(self._value)

    @classmethod
    def _from_string(cls, serialized):
        if not serialized.startswith('0x'):
            raise InvalidKeyError(serialized)
        try:
            return cls(int(serialized, 16))
        except (ValueError, TypeError):
            raise InvalidKeyError(serialized)


class Base10Key(DummyKey):
    def _to_string(self):
        return unicode(self._value)

    @classmethod
    def _from_string(cls, serialized):
        try:
            return cls(int(serialized))
        except (ValueError, TypeError):
            raise InvalidKeyError(serialized)


class KeyTests(TestCase):
    def test_namespace_from_string(self):
        hex_key = DummyKey.from_string('hex:0x10')
        self.assertIsInstance(hex_key, HexKey)
        self.assertEquals(hex_key._value, 16)

        base_key = DummyKey.from_string('base10:15')
        self.assertIsInstance(base_key, Base10Key)
        self.assertEquals(base_key._value, 15)

    def test_unknown_namespace(self):
        with self.assertRaises(InvalidKeyError):
            DummyKey.from_string('no_namespace:0x10')

    def test_no_namespace_from_string(self):
        hex_key = DummyKey.from_string('0x10')
        self.assertIsInstance(hex_key, HexKey)
        self.assertEquals(hex_key._value, 16)

        base_key = DummyKey.from_string('15')
        self.assertIsInstance(base_key, Base10Key)
        self.assertEquals(base_key._value, 15)
