"""
Tests of AsideUsageKeyV1 and AsideDefinitionKeyV1.
"""

import itertools
from unittest import TestCase

import ddt
from hypothesis import HealthCheck, assume, given, settings, strategies

from opaque_keys.edx.asides import (
    AsideUsageKeyV1, AsideDefinitionKeyV1,
    AsideUsageKeyV2, AsideDefinitionKeyV2,
    _encode_v1, _decode_v1, _join_keys_v1, _split_keys_v1,
    _encode_v2, _decode_v2, _join_keys_v2, _split_keys_v2
)
from opaque_keys.edx.keys import AsideUsageKey, AsideDefinitionKey
from opaque_keys.edx.locations import Location
from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator, DefinitionLocator


ENCODING_TEXT = strategies.lists(
    strategies.one_of(
        strategies.text('$:'),
        strategies.text(),
    )
).map(''.join)


@ddt.ddt
class TestEncode(TestCase):
    """Tests of encoding and decoding functions."""

    @given(text=ENCODING_TEXT)
    @settings(suppress_health_check=[HealthCheck.too_slow])
    def test_encode_v1_roundtrip(self, text):
        """
        Test all combinations that include characters we're trying to encode, or using in the encoding.
        """
        encoded = _encode_v1(text)
        decoded = _decode_v1(encoded)
        self.assertEqual(text, decoded)

    @given(left=ENCODING_TEXT, right=ENCODING_TEXT)
    @settings(suppress_health_check=[HealthCheck.too_slow])
    def test_join_v1_roundtrip(self, left, right):
        assume(not left.endswith(':'))
        assume('::' not in left)
        joined = _join_keys_v1(left, right)
        (_left, _right) = _split_keys_v1(joined)
        self.assertEqual((left, right), (_left, _right))

    @given(text=ENCODING_TEXT)
    @settings(suppress_health_check=[HealthCheck.too_slow])
    def test_decode_v1_roundtrip(self, text):
        """
        Test all combinations that include characters we're trying to encode, or using in the encoding.
        """
        try:
            decoded = _decode_v1(text)
        except ValueError:
            pass
        else:
            encoded = _encode_v1(decoded)
            self.assertEqual(text, encoded)

    @given(text=ENCODING_TEXT)
    @settings(suppress_health_check=[HealthCheck.too_slow])
    def test_encode_v2_roundtrip(self, text):
        """
        Test all combinations that include characters we're trying to encode, or using in the encoding.
        """
        encoded = _encode_v2(text)
        decoded = _decode_v2(encoded)
        self.assertEqual(text, decoded)

    @given(text=ENCODING_TEXT)
    @settings(suppress_health_check=[HealthCheck.too_slow])
    def test_decode_v2_roundtrip(self, text):
        """
        Test all combinations that include characters we're trying to encode, or using in the encoding.
        """
        try:
            decoded = _decode_v2(text)
        except ValueError:
            pass
        else:
            encoded = _encode_v2(decoded)
            self.assertEqual(text, encoded)

    @given(left=ENCODING_TEXT, right=ENCODING_TEXT)
    @settings(suppress_health_check=[HealthCheck.too_slow])
    def test_join_v2_roundtrip(self, left, right):
        joined = _join_keys_v2(left, right)
        (_left, _right) = _split_keys_v2(joined)
        self.assertEqual((left, right), (_left, _right))

    @ddt.data(
        ('$$', '$'),
        ('$$$$', '$$'),
        (':', ':'),
        ('1:', '1:'),
    )
    @ddt.unpack
    def test_valid_v1_decoding(self, string, result):
        self.assertEqual(_decode_v1(string), result)

    @ddt.data(
        ('$$', '$'),
        ('$$$$', '$$'),
        ('$:', ':'),
        ('1$:', '1:'),
    )
    @ddt.unpack
    def test_valid_v2_decoding(self, string, result):
        self.assertEqual(_decode_v2(string), result)


@ddt.ddt
class TestAsideKeys(TestCase):
    """Test of Aside keys."""
    @ddt.data(*itertools.product([
        AsideUsageKeyV1,
        AsideUsageKeyV2,
    ], [
        Location.from_string('i4x://org/course/cat/name'),
        BlockUsageLocator(CourseLocator('org', 'course', 'run'), 'block_type', 'block_id'),
    ], [
        'aside',
        'aside_b'
    ]))
    @ddt.unpack
    def test_usage_round_trip_deserialized(self, key_class, usage_key, aside_type):
        key = key_class(usage_key, aside_type)
        serialized = str(key)
        deserialized = AsideUsageKey.from_string(serialized)
        self.assertEqual(key, deserialized)
        self.assertEqual(usage_key, key.usage_key, usage_key)
        self.assertEqual(usage_key, deserialized.usage_key)
        self.assertEqual(aside_type, key.aside_type)
        self.assertEqual(aside_type, deserialized.aside_type)

    @ddt.data(
        'aside-usage-v1:i4x://org/course/cat/name::aside',
        'aside-usage-v1:block-v1:org+course+cat+type@block_type+block@name::aside',
        'aside-usage-v2:lib-block-v1$:$:+-+branch@-+version@000000000000000000000000+type@-+block@-::0',
        'aside-usage-v2:i4x$://-/-/-/$:$:-::0',
        'aside-usage-v2:i4x$://-/-/-/$:$:$:-::0',
        'aside-usage-v2:i4x$://-/-/$:$:$:$:$:/-::0',
    )
    def test_usage_round_trip_serialized(self, aside_key):
        deserialized = AsideUsageKey.from_string(aside_key)
        serialized = str(deserialized)
        self.assertEqual(aside_key, serialized)

    @ddt.data(*itertools.product([
        AsideDefinitionKeyV1,
        AsideDefinitionKeyV2,
    ], [
        DefinitionLocator('block_type', 'abcd1234abcd1234abcd1234'),
    ], [
        'aside',
        'aside_b'
    ]))
    @ddt.unpack
    def test_definition_round_trip_deserialized(self, key_class, definition_key, aside_type):
        key = key_class(definition_key, aside_type)
        serialized = str(key)
        deserialized = AsideDefinitionKey.from_string(serialized)
        self.assertEqual(key, deserialized)
        self.assertEqual(definition_key, key.definition_key, definition_key)
        self.assertEqual(definition_key, deserialized.definition_key)
        self.assertEqual(aside_type, key.aside_type)
        self.assertEqual(aside_type, deserialized.aside_type)

    @ddt.data(
        'aside-def-v1:def-v1:abcd1234abcd1234abcd1234+type@block_type::aside',
        'aside-def-v2:def-v1$:abcd1234abcd1234abcd1234+type@block_type::aside'
    )
    def test_definition_round_trip_serialized(self, aside_key):
        deserialized = AsideDefinitionKey.from_string(aside_key)
        serialized = str(deserialized)
        self.assertEqual(aside_key, serialized)

    @ddt.data(*itertools.product([
        AsideUsageKeyV1,
        AsideUsageKeyV2,
    ], [
        ('aside_type', 'bside'),
        ('usage_key', BlockUsageLocator(CourseLocator('borg', 'horse', 'gun'), 'lock_type', 'lock_id')),
        ('block_id', 'lock_id'),
        ('block_type', 'lock_type'),
        # BlockUsageLocator can't `replace` a definition_key, so skip for now
        # ('definition_key', DefinitionLocator('block_type', 'abcd1234abcd1234abcd1234')),
        ('course_key', CourseLocator('borg', 'horse', 'gun')),
    ]))
    @ddt.unpack
    def test_usage_key_replace(self, key_class, attr_value):
        attr, value = attr_value
        key = key_class(
            BlockUsageLocator(CourseLocator('org', 'course', 'run'), 'block_type', 'block_id'),
            'aside'
        )
        new_key = key.replace(**{attr: value})
        self.assertEqual(getattr(new_key, attr), value)

    @ddt.data(*itertools.product([
        AsideDefinitionKeyV1,
        AsideDefinitionKeyV2,
    ], [
        ('aside_type', 'bside'),
        ('definition_key', DefinitionLocator('block_type', 'abcd1234abcd1234abcd1234')),
        ('block_type', 'lock_type'),
    ]))
    @ddt.unpack
    def test_definition_key_replace(self, key_class, attr_value):
        attr, value = attr_value
        key = key_class(DefinitionLocator('block_type', 'abcd1234abcd1234abcd1234'), 'aside')
        new_key = key.replace(**{attr: value})
        self.assertEqual(getattr(new_key, attr), value)
