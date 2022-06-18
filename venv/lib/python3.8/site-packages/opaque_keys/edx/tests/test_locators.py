"""
Tests for opaque_keys.edx.locator.
"""

import random
from unittest import TestCase
from uuid import UUID

import ddt
from bson.objectid import ObjectId

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import DefinitionKey
from opaque_keys.edx.locator import Locator, BundleDefinitionLocator, CourseLocator, DefinitionLocator, VersionTree


class LocatorTests(TestCase):
    """
    Tests for :class:`.Locator`
    """

    def test_cant_instantiate_abstract_class(self):
        self.assertRaises(TypeError, Locator)


class DefinitionLocatorTests(TestCase):
    """
    Tests for :class:`.DefinitionLocator`
    """

    def test_description_locator_url(self):
        random_value = random.randrange(16 ** 24)
        object_id = f'{random_value:024x}'
        definition_locator = DefinitionLocator('html', object_id)
        self.assertEqual(f'def-v1:{object_id}+{DefinitionLocator.BLOCK_TYPE_PREFIX}@html',
                         str(definition_locator))
        self.assertEqual(definition_locator, DefinitionKey.from_string(str(definition_locator)))

    def test_description_locator_version(self):
        random_value = random.randrange(16 ** 24)
        object_id = f'{random_value:024x}'
        definition_locator = DefinitionLocator('html', object_id)
        self.assertEqual(object_id, str(definition_locator.version))


@ddt.ddt
class BundleDefinitionLocatorTests(TestCase):
    """
    Tests for :class:`.BundleDefinitionLocator`
    """
    @ddt.data(
        'bundle-olx:4b33677f-7eb7-4376-8752-024ce057d7e8:5:html:html/introduction/definition.xml',
        'bundle-olx:22825172-cde7-4fbd-ac03-a45b631e8e65:studio_draft:video:video/v1/definition.xml',
    )
    def test_roundtrip_from_string(self, key):
        def_key = DefinitionKey.from_string(key)
        serialized = str(def_key)
        self.assertEqual(key, serialized)

    @ddt.data(
        {
            "bundle_uuid": "4b33677f-7eb7-4376-8752-024ce057d7e8",  # string but will be converted to UUID automatically
            "block_type": "video",
            "olx_path": "video/vid_001/definition.xml",
            "bundle_version": 15,
        },
        {
            "bundle_uuid": UUID("4b33677f-7eb7-4376-8752-024ce057d7e8"),
            "block_type": "video",
            "olx_path": "video/vid_001/definition.xml",
            "draft_name": "studio_draft",
        },
        {
            "bundle_uuid": UUID("4b33677f-7eb7-4376-8752-024ce057d7e8"),
            "block_type": "video",
            "olx_path": "video/θήτα/definition.xml",
            "draft_name": "studio_draft",
        },
    )
    def test_roundtrip_from_key(self, key_args):
        key = BundleDefinitionLocator(**key_args)
        serialized = str(key)
        deserialized = DefinitionKey.from_string(serialized)
        self.assertEqual(key, deserialized)

    @ddt.data(
        {
            "bundle_uuid": "not-a-valid-uuid",
            "block_type": "video",
            "olx_path": "video/vid_001/definition.xml",
            "bundle_version": 15,
        },
        {
            "bundle_uuid": UUID("4b33677f-7eb7-4376-8752-024ce057d7e8"),
            "block_type": "video",
            "olx_path": "video/vid_001/definition.xml",
            # Missing bundle_version or draft_name
        },
        {
            "bundle_uuid": UUID("4b33677f-7eb7-4376-8752-024ce057d7e8"),
            "block_type": "video",
            "olx_path": "video/vid_001/definition.xml",
            # Both bundle_version and draft_name:
            "bundle_version": 15,
            "draft_name": "studio_draft",
        },
        {
            "bundle_uuid": UUID("4b33677f-7eb7-4376-8752-024ce057d7e8"),
            "block_type": "colon:in:type",
            "olx_path": "video/vid_001/definition.xml",
            "draft_name": "studio_draft",
        },
        {
            "bundle_uuid": UUID("4b33677f-7eb7-4376-8752-024ce057d7e8"),
            "block_type": "video",
            "olx_path": "https://www.example.com",  # not a valid OLX path
            "draft_name": "studio_draft",
        },
    )
    def test_invalid_args(self, key_args):
        with self.assertRaises((InvalidKeyError, TypeError, ValueError)):
            BundleDefinitionLocator(**key_args)


class VersionTreeTests(TestCase):
    """
    Tests for :class:`.VersionTree`
    """

    def test_version_tree(self):
        """
        Test making a VersionTree object.
        """
        with self.assertRaises(TypeError):
            VersionTree("invalid")

        versionless_locator = CourseLocator(org="mit.eecs", course="6.002x", run="2014")
        with self.assertRaises(ValueError):
            VersionTree(versionless_locator)

        test_id_loc = '519665f6223ebd6980884f2b'
        test_id = ObjectId(test_id_loc)
        valid_locator = CourseLocator(version_guid=test_id)
        self.assertEqual(VersionTree(valid_locator).children, [])
