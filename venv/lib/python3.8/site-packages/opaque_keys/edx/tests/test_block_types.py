"""
Tests of BlockTypeKey subclasses.
"""
from unittest import TestCase

import ddt

from opaque_keys import InvalidKeyError
from opaque_keys.edx.block_types import BlockTypeKeyV1
from opaque_keys.edx.keys import BlockTypeKey


@ddt.ddt
class TestBlockTypeKeysV1(TestCase):
    """
    Tests of BlockTypeKeysV1.
    """

    @ddt.data('problem', 'html', 'vertical')
    def test_parse_deprecated_type(self, key):
        block_type = BlockTypeKey.from_string(key)
        self.assertEqual(key, block_type.block_type)
        self.assertEqual('xblock.v1', block_type.block_family)

    @ddt.data('problem', 'html', 'vertical')
    def test_deprecated_roundtrip(self, key):
        block_type = BlockTypeKey.from_string(key)
        serialized = str(block_type)
        self.assertEqual(key, serialized)

    def test_deprecated_construction(self):
        block_type = BlockTypeKeyV1('xblock.v1', 'problem')
        serialized = str(block_type)
        self.assertEqual('problem', serialized)

    def test_deprecated_equality(self):
        self.assertEqual(
            BlockTypeKeyV1('xblock.v1', 'problem'),
            BlockTypeKeyV1('xmodule.v1', 'problem')
        )

    @ddt.data(
        'block-type-v1:xblock_asides.v1:acid_aside',
        'block-type-v1:xblock_lytic.v1:test_analytic',
    )
    def test_roundtrip_from_string(self, key):
        block_type = BlockTypeKey.from_string(key)
        serialized = str(block_type)
        self.assertEqual(key, serialized)

    @ddt.data(
        ('xblock.v1', 'problem'),
        ('xblock_asides.v1', 'acid_aside'),
        ('xblock_lytic.v1', 'test_analytic'),
    )
    @ddt.unpack
    def test_roundtrip_from_key(self, family, block_type):
        key = BlockTypeKeyV1(family, block_type)
        serialized = str(key)
        deserialized = BlockTypeKey.from_string(serialized)
        self.assertEqual(key, deserialized)

    def test_prevent_slash_in_family(self):
        with self.assertRaises(InvalidKeyError):
            BlockTypeKeyV1('foo:bar', 'baz')
