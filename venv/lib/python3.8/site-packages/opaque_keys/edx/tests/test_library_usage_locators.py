"""
Tests of LibraryUsageLocator
"""

import itertools  # pylint: disable=wrong-import-order
from unittest import TestCase

import ddt
from bson.objectid import ObjectId

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import (
    BlockUsageLocator,
    LibraryLocator,
    LibraryLocatorV2,
    LibraryUsageLocator,
    LibraryUsageLocatorV2,
)
from opaque_keys.edx.tests import LocatorBaseTest

BLOCK_PREFIX = BlockUsageLocator.BLOCK_PREFIX
BLOCK_TYPE_PREFIX = BlockUsageLocator.BLOCK_TYPE_PREFIX
VERSION_PREFIX = BlockUsageLocator.VERSION_PREFIX


@ddt.ddt
class TestLibraryUsageLocators(LocatorBaseTest):
    """
    Tests of :class:`.LibraryUsageLocator`
    """
    @ddt.data(
        f"lib-block-v1:org+lib+{BLOCK_TYPE_PREFIX}@category+{BLOCK_PREFIX}@name",
        f"lib-block-v1:org+lib+{VERSION_PREFIX}@519665f6223ebd6980884f2b+{BLOCK_TYPE_PREFIX}"
        f"@category+{BLOCK_PREFIX}@name",
        f"lib-block-v1:org+lib+{LibraryLocator.BRANCH_PREFIX}@revision+{BLOCK_TYPE_PREFIX}@category+{BLOCK_PREFIX}@name"
    )
    def test_string_roundtrip(self, url):
        self.assertEqual(
            url,
            str(UsageKey.from_string(url))
        )

    @ddt.data(
        ("TestX", "lib3", "html", "html17"),
        ("ΩmegaX", "Ωμέγα", "html", "html15"),
    )
    @ddt.unpack
    def test_constructor(self, org, lib, block_type, block_id):
        lib_key = LibraryLocator(org=org, library=lib)
        lib_usage_key = LibraryUsageLocator(library_key=lib_key, block_type=block_type, block_id=block_id)
        lib_usage_key2 = UsageKey.from_string(
            f"lib-block-v1:{org}+{lib}+{BLOCK_TYPE_PREFIX}"
            f"@{block_type}+{BLOCK_PREFIX}@{block_id}"
        )
        self.assertEqual(lib_usage_key, lib_usage_key2)
        self.assertEqual(lib_usage_key.library_key, lib_key)
        self.assertEqual(lib_usage_key.library_key, lib_key)
        self.assertEqual(lib_usage_key.branch, None)
        self.assertEqual(lib_usage_key.run, LibraryLocator.RUN)
        self.assertIsInstance(lib_usage_key2, LibraryUsageLocator)
        self.assertIsInstance(lib_usage_key2.library_key, LibraryLocator)

    def test_no_deprecated_support(self):
        lib_key = LibraryLocator(org="TestX", library="problem-bank-15")
        with self.assertRaises(InvalidKeyError):
            LibraryUsageLocator(library_key=lib_key, block_type="html", block_id="html1", deprecated=True)

    @ddt.data(
        {'block_type': 'html', 'block_id': ''},
        {'block_type': '', 'block_id': 'html15'},
        {'block_type': '+$%@', 'block_id': 'html15'},
        {'block_type': 'html', 'block_id': '+$%@'},
    )
    def test_constructor_invalid(self, kwargs):
        lib_key = LibraryLocator(org="TestX", library="problem-bank-15")
        with self.assertRaises(InvalidKeyError):
            LibraryUsageLocator(library_key=lib_key, **kwargs)

    @ddt.data(
        f"lib-block-v1:org+lib+{BLOCK_TYPE_PREFIX}@category",
    )
    def test_constructor_invalid_from_string(self, url):
        with self.assertRaises(InvalidKeyError):
            UsageKey.from_string(url)

    @ddt.data(*itertools.product(
        (
            f"lib-block-v1:org+lib+{BLOCK_TYPE_PREFIX}@category+{BLOCK_PREFIX}@name{{}}",
            f"lib-block-v1:org+lib+{VERSION_PREFIX}"
            f"@519665f6223ebd6980884f2b+{BLOCK_TYPE_PREFIX}@category+{BLOCK_PREFIX}"
            f"@name{{}}",
            f"lib-block-v1:org+lib+{LibraryLocator.BRANCH_PREFIX}"
            f"@revision+{BLOCK_TYPE_PREFIX}@category+{BLOCK_PREFIX}"
            f"@name{{}}",
        ),
        ('\n', '\n\n', ' ', '   ', '   \n'),
    ))
    @ddt.unpack
    def test_constructor_invalid_from_string_trailing_whitespace(self, locator_fmt, whitespace):
        with self.assertRaises(InvalidKeyError):
            UsageKey.from_string(locator_fmt.format(whitespace))

    def test_superclass_make_relative(self):
        lib_key = LibraryLocator(org="TestX", library="problem-bank-15")
        obj = BlockUsageLocator.make_relative(lib_key, "block_type", "block_id")
        self.assertIsInstance(obj, LibraryUsageLocator)

    def test_replace(self):
        # pylint: disable=no-member
        org1, lib1, block_type1, block_id1 = "org1", "lib1", "type1", "id1"
        lib_key1 = LibraryLocator(org=org1, library=lib1)
        usage1 = LibraryUsageLocator(library_key=lib_key1, block_type=block_type1, block_id=block_id1)
        self.assertEqual(usage1.org, org1)
        self.assertEqual(usage1.library_key, lib_key1)

        org2, lib2 = "org2", "lib2"
        lib_key2 = LibraryLocator(org=org2, library=lib2)
        usage2 = usage1.replace(library_key=lib_key2)
        self.assertEqual(usage2.library_key, lib_key2)
        self.assertEqual(usage2.course_key, lib_key2)
        self.assertEqual(usage2.block_type, block_type1)  # Unchanged
        self.assertEqual(usage2.block_id, block_id1)  # Unchanged

        block_id3 = "id3"
        lib3 = "lib3"
        usage3 = usage1.replace(block_id=block_id3, library=lib3)
        self.assertEqual(usage3.library_key.org, org1)
        self.assertEqual(usage3.library_key.library, lib3)
        self.assertEqual(usage2.block_type, block_type1)  # Unchanged
        self.assertEqual(usage3.block_id, block_id3)

        lib_key4 = LibraryLocator(org="org4", library="lib4")
        usage4 = usage1.replace(course_key=lib_key4)
        self.assertEqual(usage4.library_key, lib_key4)
        self.assertEqual(usage4.course_key, lib_key4)
        self.assertEqual(usage4.block_type, block_type1)  # Unchanged
        self.assertEqual(usage4.block_id, block_id1)  # Unchanged

        usage5a = usage1.replace(version='aaaaaaaaaaaaaaaaaaaaaaaa')
        usage5b = usage1.replace(version_guid=ObjectId('bbbbbbbbbbbbbbbbbbbbbbbb'))
        usage5c = usage1.for_version(ObjectId('cccccccccccccccccccccccc'))
        self.assertEqual(usage5a.library_key.version_guid, ObjectId('aaaaaaaaaaaaaaaaaaaaaaaa'))
        self.assertEqual(usage5b.course_key.version_guid, ObjectId('bbbbbbbbbbbbbbbbbbbbbbbb'))
        self.assertEqual(usage5c.version_guid, ObjectId('cccccccccccccccccccccccc'))
        self.assertEqual(usage5a.block_type, block_type1)  # Unchanged
        self.assertEqual(usage5a.block_id, block_id1)  # Unchanged
        self.assertEqual(usage5b.block_type, block_type1)  # Unchanged
        self.assertEqual(usage5b.block_id, block_id1)  # Unchanged
        self.assertEqual(usage5c.block_type, block_type1)  # Unchanged
        self.assertEqual(usage5c.block_id, block_id1)  # Unchanged

        usage6 = usage5a.version_agnostic()
        self.assertEqual(usage6, usage1)

        usage7 = usage1.for_branch('tribble')
        self.assertEqual(usage7.branch, 'tribble')
        self.assertEqual(usage7.library_key.branch, 'tribble')

    def test_lib_usage_locator_no_deprecated_support(self):
        with self.assertRaises(NotImplementedError):
            LibraryUsageLocator._from_deprecated_string("1/2/3")  # pylint: disable=protected-access

        lib_key = LibraryLocator(org="TestX", library="lib")
        usage = LibraryUsageLocator(library_key=lib_key, block_type="html", block_id="123")
        with self.assertRaises(NotImplementedError):
            usage._to_deprecated_string()  # pylint: disable=protected-access

        with self.assertRaises(NotImplementedError):
            LibraryUsageLocator._from_deprecated_son("", "")  # pylint: disable=protected-access

        with self.assertRaises(NotImplementedError):
            usage.to_deprecated_son()


@ddt.ddt
class LibraryUsageLocatorV2Tests(TestCase):
    """
    Tests for :class:`.LibraryUsageLocatorV2`
    """
    VALID_LIB_KEY = LibraryLocatorV2("SchoolX", "lib-slug")

    def test_inheritance(self):
        """
        A LibraryUsageLocatorV2 is a usage key
        """
        usage_key = LibraryUsageLocatorV2(self.VALID_LIB_KEY, "problem", "p1")
        self.assertIsInstance(usage_key, UsageKey)

    @ddt.data(
        'lb:MITx:reallyhardproblems:problem:problem1',
        'lb:edX:demo-lib.2019:html:introduction',
        'lb:UnicodeX:i18n-lib:html:έψιλον',
    )
    def test_roundtrip_from_string(self, key):
        usage_key = UsageKey.from_string(key)
        serialized = str(usage_key)
        self.assertEqual(key, serialized)

    @ddt.data(
        {"lib_key": VALID_LIB_KEY, "block_type": "video", "usage_id": "vid-a4"},
        {"lib_key": VALID_LIB_KEY, "block_type": "problem", "usage_id": "p1"},
        {"lib_key": VALID_LIB_KEY, "block_type": "problem", "usage_id": "1"},
    )
    def test_roundtrip_from_key(self, key_args):
        key = LibraryUsageLocatorV2(**key_args)
        serialized = str(key)
        deserialized = UsageKey.from_string(serialized)
        self.assertEqual(key, deserialized)

    @ddt.data(
        # Keys with invalid lib_key:
        {"lib_key": "lib:SchoolX:this-is-a-string", "block_type": "problem", "usage_id": "p1"},
        {"lib_key": "foobar", "block_type": "problem", "usage_id": "p1"},
        {"lib_key": None, "block_type": "problem", "usage_id": "p1"},
        # Keys with invalid block_type:
        {"lib_key": VALID_LIB_KEY, "block_type": None, "usage_id": "vid-a4"},
        {"lib_key": VALID_LIB_KEY, "block_type": "a b", "usage_id": "vid-a4"},
        # Keys with invalid usage_id:
        {"lib_key": VALID_LIB_KEY, "block_type": "video", "usage_id": None},
        {"lib_key": VALID_LIB_KEY, "block_type": "video", "usage_id": ""},
        {"lib_key": VALID_LIB_KEY, "block_type": "video", "usage_id": "a b c"},
        {"lib_key": VALID_LIB_KEY, "block_type": "video", "usage_id": "$!%^"},
        {"lib_key": VALID_LIB_KEY, "block_type": "video", "usage_id": 1},
    )
    def test_invalid_args(self, key_args):
        with self.assertRaises((InvalidKeyError, TypeError, ValueError)):
            LibraryUsageLocatorV2(**key_args)

    def test_map_into_course(self):
        """
        Test that key.map_into_course(key.course_key) won't raise an error as
        this pattern is used in several places in the LMS that still support
        old mongo.
        """
        key = LibraryUsageLocatorV2(self.VALID_LIB_KEY, block_type="problem", usage_id="p1")
        self.assertEqual(key.map_into_course(key.course_key), key)
