"""
Tests for `field_overrides` module.
"""
import unittest

from django.test import TestCase
from django.test.utils import override_settings
from xblock.field_data import DictFieldData

from ..field_overrides import (
    disable_overrides,
    FieldOverrideProvider,
    OverrideFieldData,
    resolve_dotted,
)


TESTUSER = "testuser"


@override_settings(FIELD_OVERRIDE_PROVIDERS=(
    'courseware.tests.test_field_overrides.TestOverrideProvider',))
class OverrideFieldDataTests(TestCase):
    """
    Tests for `OverrideFieldData`.
    """

    def setUp(self):
        super(OverrideFieldDataTests, self).setUp()
        OverrideFieldData.provider_classes = None

    def tearDown(self):
        super(OverrideFieldDataTests, self).tearDown()
        OverrideFieldData.provider_classes = None

    def make_one(self):
        """
        Factory method.
        """
        return OverrideFieldData.wrap(TESTUSER, DictFieldData({
            'foo': 'bar',
            'bees': 'knees',
        }))

    def test_get(self):
        data = self.make_one()
        self.assertEqual(data.get('block', 'foo'), 'fu')
        self.assertEqual(data.get('block', 'bees'), 'knees')
        with disable_overrides():
            self.assertEqual(data.get('block', 'foo'), 'bar')

    def test_set(self):
        data = self.make_one()
        data.set('block', 'foo', 'yowza')
        self.assertEqual(data.get('block', 'foo'), 'fu')
        with disable_overrides():
            self.assertEqual(data.get('block', 'foo'), 'yowza')

    def test_delete(self):
        data = self.make_one()
        data.delete('block', 'foo')
        self.assertEqual(data.get('block', 'foo'), 'fu')
        with disable_overrides():
            # Since field_data is responsible for attribute access, you'd
            # expect it to raise AttributeError. In fact, it raises KeyError,
            # so we check for that.
            with self.assertRaises(KeyError):
                data.get('block', 'foo')

    def test_has(self):
        data = self.make_one()
        self.assertTrue(data.has('block', 'foo'))
        self.assertTrue(data.has('block', 'bees'))
        self.assertTrue(data.has('block', 'oh'))
        with disable_overrides():
            self.assertFalse(data.has('block', 'oh'))

    def test_many(self):
        data = self.make_one()
        data.set_many('block', {'foo': 'baz', 'ah': 'ic'})
        self.assertEqual(data.get('block', 'foo'), 'fu')
        self.assertEqual(data.get('block', 'ah'), 'ic')
        with disable_overrides():
            self.assertEqual(data.get('block', 'foo'), 'baz')

    @override_settings(FIELD_OVERRIDE_PROVIDERS=())
    def test_no_overrides_configured(self):
        data = self.make_one()
        self.assertIsInstance(data, DictFieldData)


class ResolveDottedTests(unittest.TestCase):
    """
    Tests for `resolve_dotted`.
    """

    def test_bad_sub_import(self):
        with self.assertRaises(ImportError):
            resolve_dotted('courseware.tests.test_foo')

    def test_bad_import(self):
        with self.assertRaises(ImportError):
            resolve_dotted('nosuchpackage')

    def test_import_something_that_isnt_already_loaded(self):
        self.assertEqual(
            resolve_dotted('courseware.tests.animport.SOMENAME'),
            'bar'
        )


class TestOverrideProvider(FieldOverrideProvider):
    """
    A concrete implementation of `FieldOverrideProvider` for testing.
    """
    def get(self, block, name, default):
        assert self.user is TESTUSER
        assert block == 'block'
        if name == 'foo':
            return 'fu'
        if name == 'oh':
            return 'man'
        return default
