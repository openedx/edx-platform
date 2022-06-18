"""
Tests of LibraryLocators
"""

import itertools  # pylint: disable=wrong-import-order
from unittest import TestCase

import ddt
from bson.objectid import ObjectId

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, LearningContextKey
from opaque_keys.edx.locator import LibraryUsageLocator, LibraryLocator, LibraryLocatorV2, CourseLocator, AssetLocator
from opaque_keys.edx.tests import LocatorBaseTest, TestDeprecated


@ddt.ddt
class TestLibraryLocators(LocatorBaseTest, TestDeprecated):
    """
    Tests of :class:`.LibraryLocator`
    """
    @ddt.data(
        "org/lib/run/foo",
        "org/lib",
        "org+lib+run",
        "org+lib+",
        "org+lib++branch@library",
        "org+ne@t",
        "per%ent+sign",
    )
    def test_lib_key_from_invalid_string(self, lib_id_str):
        with self.assertRaises(InvalidKeyError):
            LibraryLocator.from_string(lib_id_str)

    @ddt.data(*itertools.product(
        (
            "library-v1:TestX+LibY{}",
        ),
        ('\n', '\n\n', ' ', '   ', '   \n'),
    ))
    @ddt.unpack
    def test_lib_key_with_trailing_whitespace(self, lib_id_fmt, whitespace):
        with self.assertRaises(InvalidKeyError):
            LibraryLocator.from_string(lib_id_fmt.format(whitespace))

    def test_lib_key_constructor(self):
        org = 'TestX'
        code = 'test-problem-bank'
        lib_key = LibraryLocator(org=org, library=code)
        self.assertEqual(lib_key.org, org)
        self.assertEqual(lib_key.library, code)  # pylint: disable=no-member
        with self.assertDeprecationWarning():
            self.assertEqual(lib_key.course, code)
        with self.assertDeprecationWarning():
            self.assertEqual(lib_key.run, 'library')
        self.assertEqual(lib_key.branch, None)  # pylint: disable=no-member

    def test_constructor_using_course(self):
        org = 'TestX'
        code = 'test-problem-bank'
        lib_key = LibraryLocator(org=org, library=code)
        with self.assertDeprecationWarning():
            lib_key2 = LibraryLocator(org=org, course=code)
        self.assertEqual(lib_key, lib_key2)
        self.assertEqual(lib_key2.library, code)  # pylint: disable=no-member

    def test_version_property_deprecated(self):
        lib_key = CourseKey.from_string('library-v1:TestX+lib1+version@519665f6223ebd6980884f2b')
        with self.assertDeprecationWarning():
            self.assertEqual(lib_key.version, ObjectId('519665f6223ebd6980884f2b'))

    def test_invalid_run(self):
        with self.assertRaises(ValueError):
            LibraryLocator(org='TestX', library='test', run='not-library')

    def test_lib_key_inheritance(self):
        lib_key = CourseKey.from_string('library-v1:TestX+lib1')
        self.assertIsInstance(lib_key, CourseKey)  # In future, this may change
        self.assertNotIsInstance(lib_key, CourseLocator)

    def test_lib_key_roundtrip_and_equality(self):
        org = 'TestX'
        code = 'test-problem-bank'
        lib_key = LibraryLocator(org=org, library=code)
        lib_key2 = CourseKey.from_string(str(lib_key))
        self.assertEqual(lib_key, lib_key2)

    def test_lib_key_make_usage_key(self):
        lib_key = CourseKey.from_string('library-v1:TestX+lib1')
        usage_key = LibraryUsageLocator(lib_key, 'html', 'html17')
        made = lib_key.make_usage_key('html', 'html17')
        self.assertEqual(usage_key, made)
        self.assertEqual(
            str(usage_key),
            str(made)
        )

    def test_lib_key_not_deprecated(self):
        lib_key = CourseKey.from_string('library-v1:TestX+lib1')
        self.assertEqual(lib_key.deprecated, False)

    def test_lib_key_no_deprecated_support(self):
        lib_key = CourseKey.from_string('library-v1:TestX+lib1')
        with self.assertRaises(AttributeError):
            lib_key.to_deprecated_string()
        with self.assertRaises(NotImplementedError):
            lib_key._to_deprecated_string()  # pylint: disable=protected-access
        with self.assertRaises(NotImplementedError):
            LibraryLocator._from_deprecated_string('test/test/test')  # pylint: disable=protected-access
        with self.assertRaises(InvalidKeyError):
            LibraryLocator(org='org', library='code', deprecated=True)

    def test_lib_key_no_offering(self):
        with self.assertRaises(ValueError):
            LibraryLocator(org='TestX', library='test', offering='tribble')

    def test_lib_key_branch_support(self):
        org = 'TestX'
        code = 'test-branch-support'
        branch = 'future-purposes-perhaps'
        lib_key = LibraryLocator(org=org, library=code, branch=branch)
        self.assertEqual(lib_key.org, org)
        self.assertEqual(lib_key.library, code)  # pylint: disable=no-member
        self.assertEqual(lib_key.branch, branch)  # pylint: disable=no-member
        lib_key2 = CourseKey.from_string(str(lib_key))
        self.assertEqual(lib_key, lib_key2)
        self.assertEqual(lib_key.branch, branch)  # pylint: disable=no-member

    def test_for_branch(self):
        lib_key = LibraryLocator(org='TestX', library='test', branch='initial')

        branch2 = "br2"
        branch2_key = lib_key.for_branch(branch2)
        self.assertEqual(branch2_key.branch, branch2)  # pylint: disable=no-member

        normal_branch = lib_key.for_branch(None)
        self.assertEqual(normal_branch.branch, None)  # pylint: disable=no-member

    def test_version_only_lib_key(self):
        version_only_lib_key = LibraryLocator(version_guid=ObjectId('519665f6223ebd6980884f2b'))
        self.assertEqual(version_only_lib_key.org, None)
        self.assertEqual(version_only_lib_key.library, None)  # pylint: disable=no-member
        with self.assertRaises(InvalidKeyError):
            version_only_lib_key.for_branch("test")

    @ddt.data(
        {},
        {'branch': 'published'},
        {'library': 'lib5'},
        {'library': 'lib5', 'branch': 'published'},
        {'org': 'TestX'},
    )
    def test_lib_key_constructor_underspecified(self, constructor_kwargs):
        with self.assertRaises(InvalidKeyError):
            LibraryLocator(**constructor_kwargs)

    def test_lib_key_constructor_overspecified(self):
        with self.assertRaises(ValueError):
            LibraryLocator(org='TestX', library='big', course='small')

    def test_lib_key_constructor_bad_ids(self):
        with self.assertRaises(InvalidKeyError):
            LibraryLocator(org="!@#{$%^&*}", library="lib1")
        with self.assertRaises(InvalidKeyError):
            LibraryLocator(org="TestX", library="lib+1")
        with self.assertRaises(InvalidKeyError):
            LibraryLocator(org="TestX", library="lib1", branch="!+!")

    def test_lib_key_constructor_bad_version_guid(self):
        with self.assertRaises(InvalidKeyError):
            LibraryLocator(version_guid="012345")

        with self.assertRaises(InvalidKeyError):
            LibraryLocator(version_guid=None)

    @ddt.data(
        ObjectId(),  # generate a random version ID
        '519665f6223ebd6980884f2b'
    )
    def test_lib_key_constructor_version_guid(self, version_id):
        version_id_str = str(version_id)
        version_id_obj = ObjectId(version_id)

        lib_key = LibraryLocator(version_guid=version_id)
        self.assertEqual(lib_key.version_guid, version_id_obj)  # pylint: disable=no-member
        self.assertEqual(lib_key.org, None)
        self.assertEqual(lib_key.library, None)  # pylint: disable=no-member
        self.assertEqual(str(lib_key.version_guid), version_id_str)  # pylint: disable=no-member
        # Allow access to _to_string
        # pylint: disable=protected-access
        expected_str = '@'.join((lib_key.VERSION_PREFIX, version_id_str))
        self.assertEqual(lib_key._to_string(), expected_str)
        self.assertEqual(str(lib_key), 'library-v1:' + expected_str)
        self.assertEqual(lib_key.html_id(), 'library-v1:' + expected_str)

    def test_library_constructor_version_url(self):
        # Test parsing a url when it starts with a version ID and there is also a block ID.
        # This hits the parsers parse_guid method.
        test_id_loc = '519665f6223ebd6980884f2b'
        testobj = CourseKey.from_string(
            f"library-v1:{LibraryLocator.VERSION_PREFIX}@{test_id_loc}+{LibraryLocator.BLOCK_PREFIX}@hw3"
        )
        self.assertEqual(testobj.version_guid, ObjectId(test_id_loc))
        self.assertEqual(testobj.org, None)
        self.assertEqual(testobj.library, None)

    def test_changing_course(self):
        lib_key = LibraryLocator(org="TestX", library="test")
        with self.assertRaises(AttributeError):
            lib_key.course = "PHYS"
        with self.assertRaises(KeyError):
            lib_key.replace(course="PHYS")

    def test_make_asset_key(self):
        lib_key = CourseKey.from_string('library-v1:TestX+lib1')
        self.assertEqual(
            AssetLocator(lib_key, 'asset', 'foo.bar'),
            lib_key.make_asset_key('asset', 'foo.bar')
        )

    def test_versions(self):
        lib_key = CourseKey.from_string('library-v1:TestX+lib1+version@519665f6223ebd6980884f2b')
        lib_key2 = CourseKey.from_string('library-v1:TestX+lib1')
        lib_key3 = lib_key.version_agnostic()
        self.assertEqual(lib_key2, lib_key3)
        self.assertEqual(lib_key3.version_guid, None)

        new_version = '123445678912345678912345'
        lib_key4 = lib_key.for_version(new_version)
        self.assertEqual(lib_key4.version_guid, ObjectId(new_version))

    def test_course_agnostic(self):
        lib_key = CourseKey.from_string('library-v1:TestX+lib1+version@519665f6223ebd6980884f2b')
        lib_key2 = CourseKey.from_string('library-v1:version@519665f6223ebd6980884f2b')
        lib_key3 = lib_key.course_agnostic()
        self.assertEqual(lib_key2, lib_key3)
        self.assertEqual(lib_key3.org, None)
        self.assertEqual(lib_key3.library, None)


@ddt.ddt
class LibraryLocatorV2Tests(TestCase):
    """
    Tests for :class:`.LibraryLocatorV2`
    """

    def test_inheritance(self):
        """
        A LibraryLocatorV2 is a context key but not a coursekey
        """
        lib_key = LibraryLocatorV2("SchoolX", "lib-slug")
        self.assertIsInstance(lib_key, LearningContextKey)
        self.assertNotIsInstance(lib_key, CourseKey)
        self.assertFalse(lib_key.is_course)

    def test_from_string_inheritance(self):
        """
        Test that CourseKey.from_string(...) will never give you a library key
        unexpectedly, but LearningContextKey.from_string(...) will give you
        either.
        """
        lib_string = 'lib:MITx:reallyhardproblems'
        course_string = 'course-v1:org+course+run'
        # This should not work because lib_string is not a course key:
        with self.assertRaises(InvalidKeyError):
            CourseKey.from_string(lib_string)
        # But this should work:
        self.assertIsInstance(
            LearningContextKey.from_string(lib_string),
            LibraryLocatorV2,
        )
        # And this should work:
        self.assertIsInstance(
            LearningContextKey.from_string(course_string),
            CourseLocator,
        )

    @ddt.data(
        'lib:MITx:reallyhardproblems',
        'lib:edX:demo-lib.2019',
    )
    def test_roundtrip_from_string(self, key):
        lib_key = LearningContextKey.from_string(key)
        serialized = str(lib_key)
        self.assertEqual(key, serialized)

    @ddt.data(
        {"org": "edX", "slug": "platform-intro-videos"},
        {"org": "LunaX", "slug": "phys870-tachyon-problems"},
        {"org": "EpsilonX", "slug": "έψιλον"},  # Unicode slugs are allowed
    )
    def test_roundtrip_from_key(self, key_args):
        key = LibraryLocatorV2(**key_args)
        serialized = str(key)
        deserialized = LearningContextKey.from_string(serialized)
        self.assertEqual(key, deserialized)

    @ddt.data(
        {"org": "not a valid org", "slug": "foobar"},
        {"org": "", "slug": "foobar"},
        {"org": 123, "slug": "foobar"},
        {"org": "έψιλον", "slug": "foobar"},  # The organizations app does not allow unicode org IDs.
        {"org": "org", "slug": "not a valid slug"},
        {"org": "org", "slug": ""},
        {"org": "org", "slug": 27823478900457890},
    )
    def test_invalid_args(self, key_args):
        with self.assertRaises((InvalidKeyError, TypeError, ValueError)):
            LibraryLocatorV2(**key_args)
