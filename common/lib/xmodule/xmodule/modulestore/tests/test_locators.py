"""
Tests for xmodule.modulestore.locator.
"""
from unittest import TestCase

from bson.objectid import ObjectId
from xmodule.modulestore.locator import Locator, CourseLocator, BlockUsageLocator, DefinitionLocator
from xmodule.modulestore.parsers import BRANCH_PREFIX, BLOCK_PREFIX, VERSION_PREFIX
from xmodule.modulestore.exceptions import InsufficientSpecificationError, OverSpecificationError
from xmodule.modulestore import Location
import random


class LocatorTest(TestCase):
    """
    Tests for subclasses of Locator.
    """

    def test_cant_instantiate_abstract_class(self):
        self.assertRaises(TypeError, Locator)

    def test_course_constructor_overspecified(self):
        self.assertRaises(
            OverSpecificationError,
            CourseLocator,
            url='edx://mit.eecs+6002x',
            package_id='harvard.history',
            branch='published',
            version_guid=ObjectId())
        self.assertRaises(
            OverSpecificationError,
            CourseLocator,
            url='edx://mit.eecs+6002x',
            package_id='harvard.history',
            version_guid=ObjectId())
        self.assertRaises(
            OverSpecificationError,
            CourseLocator,
            url='edx://mit.eecs+6002x/' + BRANCH_PREFIX + 'published',
            branch='draft')
        self.assertRaises(
            OverSpecificationError,
            CourseLocator,
            package_id='mit.eecs+6002x/' + BRANCH_PREFIX + 'published',
            branch='draft')

    def test_course_constructor_underspecified(self):
        self.assertRaises(InsufficientSpecificationError, CourseLocator)
        self.assertRaises(InsufficientSpecificationError, CourseLocator, branch='published')

    def test_course_constructor_bad_version_guid(self):
        self.assertRaises(ValueError, CourseLocator, version_guid="012345")
        self.assertRaises(InsufficientSpecificationError, CourseLocator, version_guid=None)

    def test_course_constructor_version_guid(self):
        # generate a random location
        test_id_1 = ObjectId()
        test_id_1_loc = str(test_id_1)
        testobj_1 = CourseLocator(version_guid=test_id_1)
        self.check_course_locn_fields(testobj_1, 'version_guid', version_guid=test_id_1)
        self.assertEqual(str(testobj_1.version_guid), test_id_1_loc)
        self.assertEqual(str(testobj_1), VERSION_PREFIX + test_id_1_loc)
        self.assertEqual(testobj_1.url(), 'edx://' + VERSION_PREFIX + test_id_1_loc)

        # Test using a given string
        test_id_2_loc = '519665f6223ebd6980884f2b'
        test_id_2 = ObjectId(test_id_2_loc)
        testobj_2 = CourseLocator(version_guid=test_id_2)
        self.check_course_locn_fields(testobj_2, 'version_guid', version_guid=test_id_2)
        self.assertEqual(str(testobj_2.version_guid), test_id_2_loc)
        self.assertEqual(str(testobj_2), VERSION_PREFIX + test_id_2_loc)
        self.assertEqual(testobj_2.url(), 'edx://' + VERSION_PREFIX + test_id_2_loc)

    def test_course_constructor_bad_package_id(self):
        """
        Test all sorts of badly-formed package_ids (and urls with those package_ids)
        """
        for bad_id in (' mit.eecs',
                       'mit.eecs ',
                       VERSION_PREFIX + 'mit.eecs',
                       BLOCK_PREFIX + 'black/mit.eecs',
                       'mit.ee cs',
                       'mit.ee,cs',
                       'mit.ee/cs',
                       'mit.ee&cs',
                       'mit.ee()cs',
                       BRANCH_PREFIX + 'this',
                       'mit.eecs/' + BRANCH_PREFIX,
                       'mit.eecs/' + BRANCH_PREFIX + 'this/' + BRANCH_PREFIX + 'that',
                       'mit.eecs/' + BRANCH_PREFIX + 'this/' + BRANCH_PREFIX,
                       'mit.eecs/' + BRANCH_PREFIX + 'this ',
                       'mit.eecs/' + BRANCH_PREFIX + 'th%is ',
                       ):
            self.assertRaises(ValueError, CourseLocator, package_id=bad_id)
            self.assertRaises(ValueError, CourseLocator, url='edx://' + bad_id)

    def test_course_constructor_bad_url(self):
        for bad_url in ('edx://',
                        'edx:/mit.eecs',
                        'http://mit.eecs',
                        'edx//mit.eecs'):
            self.assertRaises(ValueError, CourseLocator, url=bad_url)

    def test_course_constructor_redundant_001(self):
        testurn = 'mit.eecs+6002x'
        testobj = CourseLocator(package_id=testurn, url='edx://' + testurn)
        self.check_course_locn_fields(testobj, 'package_id', package_id=testurn)

    def test_course_constructor_redundant_002(self):
        testurn = 'mit.eecs+6002x/' + BRANCH_PREFIX + 'published'
        expected_urn = 'mit.eecs+6002x'
        expected_rev = 'published'
        testobj = CourseLocator(package_id=testurn, url='edx://' + testurn)
        self.check_course_locn_fields(testobj, 'package_id',
                                      package_id=expected_urn,
                                      branch=expected_rev)

    def test_course_constructor_url(self):
        # Test parsing a url when it starts with a version ID and there is also a block ID.
        # This hits the parsers parse_guid method.
        test_id_loc = '519665f6223ebd6980884f2b'
        testobj = CourseLocator(url="edx://{}{}/{}hw3".format(VERSION_PREFIX, test_id_loc, BLOCK_PREFIX))
        self.check_course_locn_fields(
            testobj,
            'test_block constructor',
            version_guid=ObjectId(test_id_loc)
        )

    def test_course_constructor_url_package_id_and_version_guid(self):
        test_id_loc = '519665f6223ebd6980884f2b'
        testobj = CourseLocator(url='edx://mit.eecs-honors.6002x/' + VERSION_PREFIX + test_id_loc)
        self.check_course_locn_fields(testobj, 'error parsing url with both course ID and version GUID',
                                      package_id='mit.eecs-honors.6002x',
                                      version_guid=ObjectId(test_id_loc))

    def test_course_constructor_url_package_id_branch_and_version_guid(self):
        test_id_loc = '519665f6223ebd6980884f2b'
        testobj = CourseLocator(url='edx://mit.eecs.~6002x/' + BRANCH_PREFIX + 'draft-1/' + VERSION_PREFIX + test_id_loc)
        self.check_course_locn_fields(testobj, 'error parsing url with both course ID branch, and version GUID',
                                      package_id='mit.eecs.~6002x',
                                      branch='draft-1',
                                      version_guid=ObjectId(test_id_loc))

    def test_course_constructor_package_id_no_branch(self):
        testurn = 'mit.eecs+6002x'
        testobj = CourseLocator(package_id=testurn)
        self.check_course_locn_fields(testobj, 'package_id', package_id=testurn)
        self.assertEqual(testobj.package_id, testurn)
        self.assertEqual(str(testobj), testurn)
        self.assertEqual(testobj.url(), 'edx://' + testurn)

    def test_course_constructor_package_id_with_branch(self):
        testurn = 'mit.eecs+6002x/' + BRANCH_PREFIX + 'published'
        expected_id = 'mit.eecs+6002x'
        expected_branch = 'published'
        testobj = CourseLocator(package_id=testurn)
        self.check_course_locn_fields(testobj, 'package_id with branch',
                                      package_id=expected_id,
                                      branch=expected_branch,
                                      )
        self.assertEqual(testobj.package_id, expected_id)
        self.assertEqual(testobj.branch, expected_branch)
        self.assertEqual(str(testobj), testurn)
        self.assertEqual(testobj.url(), 'edx://' + testurn)

    def test_course_constructor_package_id_separate_branch(self):
        test_id = 'mit.eecs+6002x'
        test_branch = 'published'
        expected_urn = 'mit.eecs+6002x/' + BRANCH_PREFIX + 'published'
        testobj = CourseLocator(package_id=test_id, branch=test_branch)
        self.check_course_locn_fields(testobj, 'package_id with separate branch',
                                      package_id=test_id,
                                      branch=test_branch,
                                      )
        self.assertEqual(testobj.package_id, test_id)
        self.assertEqual(testobj.branch, test_branch)
        self.assertEqual(str(testobj), expected_urn)
        self.assertEqual(testobj.url(), 'edx://' + expected_urn)

    def test_course_constructor_package_id_repeated_branch(self):
        """
        The same branch appears in the package_id and the branch field.
        """
        test_id = 'mit.eecs+6002x/' + BRANCH_PREFIX + 'published'
        test_branch = 'published'
        expected_id = 'mit.eecs+6002x'
        expected_urn = test_id
        testobj = CourseLocator(package_id=test_id, branch=test_branch)
        self.check_course_locn_fields(testobj, 'package_id with repeated branch',
                                      package_id=expected_id,
                                      branch=test_branch,
                                      )
        self.assertEqual(testobj.package_id, expected_id)
        self.assertEqual(testobj.branch, test_branch)
        self.assertEqual(str(testobj), expected_urn)
        self.assertEqual(testobj.url(), 'edx://' + expected_urn)

    def test_block_constructor(self):
        testurn = 'mit.eecs+6002x/' + BRANCH_PREFIX + 'published/' + BLOCK_PREFIX + 'HW3'
        expected_id = 'mit.eecs+6002x'
        expected_branch = 'published'
        expected_block_ref = 'HW3'
        testobj = BlockUsageLocator(url=testurn)
        self.check_block_locn_fields(testobj, 'test_block constructor',
                                     package_id=expected_id,
                                     branch=expected_branch,
                                     block=expected_block_ref)
        self.assertEqual(str(testobj), testurn)
        self.assertEqual(testobj.url(), 'edx://' + testurn)
        testobj = BlockUsageLocator(url=testurn, version_guid=ObjectId())
        agnostic = testobj.version_agnostic()
        self.assertIsNone(agnostic.version_guid)
        self.check_block_locn_fields(agnostic, 'test_block constructor',
                                     package_id=expected_id,
                                     branch=expected_branch,
                                     block=expected_block_ref)

    def test_block_constructor_url_version_prefix(self):
        test_id_loc = '519665f6223ebd6980884f2b'
        testobj = BlockUsageLocator(
            url='edx://mit.eecs+6002x/{}{}/{}lab2'.format(VERSION_PREFIX, test_id_loc, BLOCK_PREFIX)
        )
        self.check_block_locn_fields(
            testobj, 'error parsing URL with version and block',
            package_id='mit.eecs+6002x',
            block='lab2',
            version_guid=ObjectId(test_id_loc)
        )
        agnostic = testobj.course_agnostic()
        self.check_block_locn_fields(
            agnostic, 'error parsing URL with version and block',
            block='lab2',
            package_id=None,
            version_guid=ObjectId(test_id_loc)
        )
        self.assertIsNone(agnostic.package_id)

    def test_block_constructor_url_kitchen_sink(self):
        test_id_loc = '519665f6223ebd6980884f2b'
        testobj = BlockUsageLocator(
            url='edx://mit.eecs+6002x/{}draft/{}{}/{}lab2'.format(
                BRANCH_PREFIX, VERSION_PREFIX, test_id_loc, BLOCK_PREFIX
            )
        )
        self.check_block_locn_fields(
            testobj, 'error parsing URL with branch, version, and block',
            package_id='mit.eecs+6002x',
            branch='draft',
            block='lab2',
            version_guid=ObjectId(test_id_loc)
        )

    def test_colon_name(self):
        """
        It seems we used to use colons in names; so, ensure they're acceptable.
        """
        package_id = 'mit.eecs-1'
        branch = 'foo'
        block_id = 'problem:with-colon~2'
        testobj = BlockUsageLocator(package_id=package_id, branch=branch, block_id=block_id)
        self.check_block_locn_fields(testobj, 'Cannot handle colon', package_id=package_id, branch=branch, block=block_id)

    def test_relative(self):
        """
        Test making a relative usage locator.
        """
        package_id = 'mit.eecs-1'
        branch = 'foo'
        baseobj = CourseLocator(package_id=package_id, branch=branch)
        block_id = 'problem:with-colon~2'
        testobj = BlockUsageLocator.make_relative(baseobj, block_id)
        self.check_block_locn_fields(
            testobj, 'Cannot make relative to course', package_id=package_id, branch=branch, block=block_id
        )
        block_id = 'completely_different'
        testobj = BlockUsageLocator.make_relative(testobj, block_id)
        self.check_block_locn_fields(
            testobj, 'Cannot make relative to block usage', package_id=package_id, branch=branch, block=block_id
        )

    def test_repr(self):
        testurn = 'mit.eecs+6002x/' + BRANCH_PREFIX + 'published/' + BLOCK_PREFIX + 'HW3'
        testobj = BlockUsageLocator(package_id=testurn)
        self.assertEqual('BlockUsageLocator("mit.eecs+6002x/branch/published/block/HW3")', repr(testobj))

    def test_old_location_helpers(self):
        """
        Test the functions intended to help with the conversion from old locations to locators
        """
        location_tuple = ('i4x', 'mit', 'eecs.6002x', 'course', 't3_2013')
        location = Location(location_tuple)
        self.assertEqual(location, Locator.to_locator_or_location(location))
        self.assertEqual(location, Locator.to_locator_or_location(location_tuple))
        self.assertEqual(location, Locator.to_locator_or_location(list(location_tuple)))
        self.assertEqual(location, Locator.to_locator_or_location(location.dict()))

        locator = BlockUsageLocator(package_id='foo.bar', branch='alpha', block_id='deep')
        self.assertEqual(locator, Locator.to_locator_or_location(locator))
        self.assertEqual(locator.as_course_locator(), Locator.to_locator_or_location(locator.as_course_locator()))
        self.assertEqual(location, Locator.to_locator_or_location(location.url()))
        self.assertEqual(locator, Locator.to_locator_or_location(locator.url()))
        self.assertEqual(locator, Locator.to_locator_or_location(locator.__dict__))

        asset_location = Location(['c4x', 'mit', 'eecs.6002x', 'asset', 'selfie.jpeg'])
        self.assertEqual(asset_location, Locator.to_locator_or_location(asset_location))
        self.assertEqual(asset_location, Locator.to_locator_or_location(asset_location.url()))

        def_location_url = "defx://version/" + '{:024x}'.format(random.randrange(16 ** 24))
        self.assertEqual(DefinitionLocator(def_location_url), Locator.to_locator_or_location(def_location_url))

        with self.assertRaises(ValueError):
            Locator.to_locator_or_location(22)
        with self.assertRaises(ValueError):
            Locator.to_locator_or_location("hello.world.not.a.url")
        self.assertIsNone(Locator.parse_url("unknown://foo.bar/baz"))

    def test_url_reverse(self):
        """
        Test the url_reverse method
        """
        locator = CourseLocator(package_id="a.fancy_course-id", branch="branch_1.2-3")
        self.assertEqual(
            '/expression/{}/format'.format(unicode(locator)),
            locator.url_reverse('expression', 'format')
        )
        self.assertEqual(
            '/expression/{}/format'.format(unicode(locator)),
            locator.url_reverse('/expression', '/format')
        )
        self.assertEqual(
            '/expression/{}'.format(unicode(locator)),
            locator.url_reverse('expression/', None)
        )
        self.assertEqual(
            '/expression/{}'.format(unicode(locator)),
            locator.url_reverse('/expression/', '')
        )

    def test_description_locator_url(self):
        object_id = '{:024x}'.format(random.randrange(16 ** 24))
        definition_locator = DefinitionLocator(object_id)
        self.assertEqual('defx://' + VERSION_PREFIX + object_id, definition_locator.url())
        self.assertEqual(definition_locator, DefinitionLocator(definition_locator.url()))

    def test_description_locator_version(self):
        object_id = '{:024x}'.format(random.randrange(16 ** 24))
        definition_locator = DefinitionLocator(object_id)
        self.assertEqual(object_id, str(definition_locator.version()))

    # ------------------------------------------------------------------
    # Utilities

    def check_course_locn_fields(self, testobj, msg, version_guid=None,
                                 package_id=None, branch=None):
        """
        Checks the version, package_id, and branch in testobj
        """
        self.assertEqual(testobj.version_guid, version_guid, msg)
        self.assertEqual(testobj.package_id, package_id, msg)
        self.assertEqual(testobj.branch, branch, msg)

    def check_block_locn_fields(self, testobj, msg, version_guid=None,
                                package_id=None, branch=None, block=None):
        """
        Does adds a block id check over and above the check_course_locn_fields tests
        """
        self.check_course_locn_fields(testobj, msg, version_guid, package_id,
                                      branch)
        self.assertEqual(testobj.block_id, block)
