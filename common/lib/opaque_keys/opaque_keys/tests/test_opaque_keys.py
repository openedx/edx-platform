import copy
import json
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
    __slots__ = ()

    @classmethod
    def _drivers(cls):
        # Set up a fake extension manager for testing
        return ExtensionManager.make_test_instance(
            [
                _mk_extension('hex', HexKey),
                _mk_extension('base10', Base10Key),
            ]
        )


class HexKey(DummyKey):
    KEY_FIELDS = ('value',)
    __slots__ = KEY_FIELDS

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
    KEY_FIELDS = ('value',)
    # Deliberately not using __slots__, to test both cases

    def _to_string(self):
        return unicode(self._value)

    @classmethod
    def _from_string(cls, serialized):
        try:
            return cls(int(serialized))
        except (ValueError, TypeError):
            raise InvalidKeyError(serialized)

class DictKey(DummyKey):
    KEY_FIELDS = ('value',)
    __slots__ = KEY_FIELDS

    def _to_string(self):
        return json.dumps(self._value)

    @classmethod
    def _from_string(cls, serialized):
        try:
            return cls(json.loads(serialized))
        except (ValueError, TypeError):
            raise InvalidKeyError(serialized)

class KeyTests(TestCase):
    def test_namespace_from_string(self):
        hex_key = DummyKey.from_string('hex:0x10')
        self.assertIsInstance(hex_key, HexKey)
        self.assertEquals(hex_key.value, 16)

        base_key = DummyKey.from_string('base10:15')
        self.assertIsInstance(base_key, Base10Key)
        self.assertEquals(base_key.value, 15)

    def test_unknown_namespace(self):
        with self.assertRaises(InvalidKeyError):
            DummyKey.from_string('no_namespace:0x10')

    def test_no_namespace_from_string(self):
        hex_key = DummyKey.from_string('0x10')
        self.assertIsInstance(hex_key, HexKey)
        self.assertEquals(hex_key.value, 16)

        base_key = DummyKey.from_string('15')
        self.assertIsInstance(base_key, Base10Key)
        self.assertEquals(base_key.value, 15)

    def test_immutability(self):
        key = HexKey(10)

        with self.assertRaises(AttributeError):
            key.value = 11

    def test_equality(self):
        self.assertEquals(DummyKey.from_string('0x10'), DummyKey.from_string('0x10'))
        self.assertNotEquals(DummyKey.from_string('0x10'), DummyKey.from_string('16'))

    def test_constructor(self):
        with self.assertRaises(TypeError):
            HexKey()

        with self.assertRaises(TypeError):
            HexKey(foo='bar')

        with self.assertRaises(TypeError):
            HexKey(10, 20)

        with self.assertRaises(TypeError):
            HexKey(value=10, bar=20)

        self.assertEquals(HexKey(10).value, 10)
        self.assertEquals(HexKey(value=10).value, 10)

    def test_replace(self):
        hex10 = HexKey(10)
        hex11 = hex10.replace(value=11)
        hex_copy = hex10.replace()

        self.assertNotEquals(id(hex10), id(hex11))
        self.assertNotEquals(id(hex10), id(hex_copy))
        self.assertNotEquals(hex10, hex11)
        self.assertEquals(hex10, hex_copy)
        self.assertEquals(HexKey(10), hex10)
        self.assertEquals(HexKey(11), hex11)

    def test_copy(self):
        original = DictKey({'foo': 'bar'})
        copied = copy.copy(original)
        deep = copy.deepcopy(original)

        self.assertEquals(original, copied)
        self.assertNotEquals(id(original), id(copied))
        self.assertEquals(id(original.value), id(copied.value))

        self.assertEquals(original, deep)
        self.assertNotEquals(id(original), id(deep))
        self.assertNotEquals(id(original.value), id(deep.value))

        self.assertEquals(copy.deepcopy([original]), [original])
