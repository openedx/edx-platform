"""
Tests for xmodule.modulestore.locator.
"""
from unittest import TestCase

import random
from bson.objectid import ObjectId
from opaque_keys import InvalidKeyError
from xmodule.modulestore.locator import Locator, CourseLocator, BlockUsageLocator, DefinitionLocator
from xmodule.modulestore.parsers import BRANCH_PREFIX, BLOCK_PREFIX, VERSION_PREFIX
from xmodule.modulestore.exceptions import InsufficientSpecificationError


class LocatorTest(TestCase):
    """
    Tests for subclasses of Locator.
    """

    def test_cant_instantiate_abstract_class(self):
        self.assertRaises(TypeError, Locator)

    def test_course_constructor_underspecified(self):
        with self.assertRaises(InsufficientSpecificationError):
            CourseLocator()
        with self.assertRaises(InsufficientSpecificationError):
            CourseLocator(branch='published')

    def test_course_constructor_bad_version_guid(self):
        with self.assertRaises(ValueError):
            CourseLocator(version_guid="012345")

        with self.assertRaises(InvalidKeyError):
            CourseLocator(version_guid=None)

    def test_course_constructor_version_guid(self):
        # generate a random location
        test_id_1 = ObjectId()
        test_id_1_loc = str(test_id_1)
        testobj_1 = CourseLocator(version_guid=test_id_1)
        self.check_course_locn_fields(testobj_1, 'version_guid', version_guid=test_id_1)
        self.assertEqual(str(testobj_1.version_guid), test_id_1_loc)
        self.assertEqual(testobj_1._to_string(), VERSION_PREFIX + test_id_1_loc)
        self.assertEqual(testobj_1.url(), 'edx://' + VERSION_PREFIX + test_id_1_loc)

        # Test using a given string
        test_id_2_loc = '519665f6223ebd6980884f2b'
        test_id_2 = ObjectId(test_id_2_loc)
        testobj_2 = CourseLocator(version_guid=test_id_2)
        self.check_course_locn_fields(testobj_2, 'version_guid', version_guid=test_id_2)
        self.assertEqual(str(testobj_2.version_guid), test_id_2_loc)
        self.assertEqual(testobj_2._to_string(), VERSION_PREFIX + test_id_2_loc)
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

            with self.assertRaises(ValueError):
                CourseLocator(org=bad_id, offering='test')

            with self.assertRaises(ValueError):
                CourseLocator(org='test', offering=bad_id)

            with self.assertRaises(ValueError):
                CourseLocator.from_string('edx://' + bad_id)

    def test_course_constructor_bad_url(self):
        for bad_url in ('edx://',
                        'edx:/mit.eecs',
                        'http://mit.eecs',
                        'edx//mit.eecs'):
            with self.assertRaises(ValueError):
                CourseLocator.from_string(bad_url)

    def test_course_constructor_url(self):
        # Test parsing a url when it starts with a version ID and there is also a block ID.
        # This hits the parsers parse_guid method.
        test_id_loc = '519665f6223ebd6980884f2b'
        testobj = CourseLocator.from_string("edx://{}{}/{}hw3".format(VERSION_PREFIX, test_id_loc, BLOCK_PREFIX))
        self.check_course_locn_fields(
            testobj,
            'test_block constructor',
            version_guid=ObjectId(test_id_loc)
        )

    def test_course_constructor_url_package_id_and_version_guid(self):
        test_id_loc = '519665f6223ebd6980884f2b'
        testobj = CourseLocator.from_string('edx://mit.eecs+honors.6002x/' + VERSION_PREFIX + test_id_loc)
        self.check_course_locn_fields(
            testobj, 'error parsing url with both course ID and version GUID',
            org='mit.eecs',
            offering='honors.6002x',
            version_guid=ObjectId(test_id_loc)
        )

    def test_course_constructor_url_package_id_branch_and_version_guid(self):
        test_id_loc = '519665f6223ebd6980884f2b'
        org = 'mit.eecs'
        offering = '~6002x'
        testobj = CourseLocator.from_string('edx://{}+{}/{}draft-1/{}{}'.format(
            org, offering, BRANCH_PREFIX, VERSION_PREFIX, test_id_loc
        ))
        self.check_course_locn_fields(
            testobj,
            'error parsing url with both course ID branch, and version GUID',
            org=org,
            offering=offering,
            branch='draft-1',
            version_guid=ObjectId(test_id_loc)
        )

    def test_course_constructor_package_id_no_branch(self):
        org = 'mit.eecs'
        offering = '6002x'
        testurn = '{}+{}'.format(org, offering)
        testobj = CourseLocator(org=org, offering=offering)
        self.check_course_locn_fields(testobj, 'package_id', org=org, offering=offering)
        self.assertEqual(testobj.package_id, testurn)
        self.assertEqual(testobj._to_string(), testurn)
        self.assertEqual(testobj.url(), 'edx://' + testurn)

    def test_course_constructor_package_id_separate_branch(self):
        org = 'mit.eecs'
        offering = '6002x'
        testurn = '{}+{}'.format(org, offering)
        test_branch = 'published'
        expected_urn = '{}+{}/{}{}'.format(org, offering, BRANCH_PREFIX, test_branch)
        testobj = CourseLocator(org=org, offering=offering, branch=test_branch)
        self.check_course_locn_fields(
            testobj,
            'package_id with separate branch',
            org=org,
            offering=offering,
            branch=test_branch,
        )
        self.assertEqual(testobj.package_id, testurn)
        self.assertEqual(testobj.branch, test_branch)
        self.assertEqual(testobj._to_string(), expected_urn)
        self.assertEqual(testobj.url(), 'edx://' + expected_urn)

    def test_block_constructor(self):
        expected_org = 'mit.eecs'
        expected_offering = '6002x'
        expected_branch = 'published'
        expected_block_ref = 'HW3'
        testurn = '{}+{}/{}{}/{}{}'.format(
            expected_org, expected_offering, BRANCH_PREFIX, expected_branch, BLOCK_PREFIX, 'HW3'
        )
        testobj = BlockUsageLocator.from_string(testurn)
        self.check_block_locn_fields(testobj, 'test_block constructor',
                                     org=expected_org,
                                     offering=expected_offering,
                                     branch=expected_branch,
                                     block=expected_block_ref)
        self.assertEqual(str(testobj), testurn)
        self.assertEqual(testobj.url(), 'edx://' + testurn)
        testobj = BlockUsageLocator(testobj.course_key.for_version(ObjectId()), testobj.block_id)
        agnostic = testobj.version_agnostic()
        self.assertIsNone(agnostic.version_guid)
        self.check_block_locn_fields(agnostic, 'test_block constructor',
                                     org=expected_org,
                                     offering=expected_offering,
                                     branch=expected_branch,
                                     block=expected_block_ref)

    def test_block_constructor_url_version_prefix(self):
        test_id_loc = '519665f6223ebd6980884f2b'
        testobj = BlockUsageLocator.from_string(
            url='edx://mit.eecs+6002x/{}{}/{}lab2'.format(VERSION_PREFIX, test_id_loc, BLOCK_PREFIX)
        )
        self.check_block_locn_fields(
            testobj, 'error parsing URL with version and block',
            org='mit.eecs',
            offering='6002x',
            block='lab2',
            version_guid=ObjectId(test_id_loc)
        )
        agnostic = testobj.course_agnostic()
        self.check_block_locn_fields(
            agnostic, 'error parsing URL with version and block',
            block='lab2',
            org=None,
            offering=None,
            version_guid=ObjectId(test_id_loc)
        )
        self.assertIsNone(agnostic.package_id)

    def test_block_constructor_url_kitchen_sink(self):
        test_id_loc = '519665f6223ebd6980884f2b'
        testobj = BlockUsageLocator.from_string(
            url='edx://mit.eecs+6002x/{}draft/{}{}/{}lab2'.format(
                BRANCH_PREFIX, VERSION_PREFIX, test_id_loc, BLOCK_PREFIX
            )
        )
        self.check_block_locn_fields(
            testobj, 'error parsing URL with branch, version, and block',
            org='mit.eecs',
            offering='6002x',
            branch='draft',
            block='lab2',
            version_guid=ObjectId(test_id_loc)
        )

    def test_colon_name(self):
        """
        It seems we used to use colons in names; so, ensure they're acceptable.
        """
        org = 'mit.eecs'
        offering = '1'
        branch = 'foo'
        block_id = 'problem:with-colon~2'
        testobj = BlockUsageLocator(org=org, offering=offering, branch=branch, block_id=block_id)
        self.check_block_locn_fields(
            testobj, 'Cannot handle colon', org=org, offering=offering, branch=branch, block=block_id
        )

    def test_relative(self):
        """
        Test making a relative usage locator.
        """
        org = 'mit.eecs'
        offering = '1'
        branch = 'foo'
        baseobj = CourseLocator(org=org, offering=offering, branch=branch)
        block_id = 'problem:with-colon~2'
        testobj = BlockUsageLocator.make_relative(baseobj, block_id)
        self.check_block_locn_fields(
            testobj, 'Cannot make relative to course', org=org, offering=offering, branch=branch, block=block_id
        )
        block_id = 'completely_different'
        testobj = BlockUsageLocator.make_relative(testobj, block_id)
        self.check_block_locn_fields(
            testobj, 'Cannot make relative to block usage', org=org, offering=offering, branch=branch, block=block_id
        )

    def test_repr(self):
        testurn = 'mit.eecs+6002x/' + BRANCH_PREFIX + 'published/' + BLOCK_PREFIX + 'HW3'
        testobj = BlockUsageLocator.from_string(testurn)
        self.assertEqual("BlockUsageLocator('mit.eecs', '6002x', 'published', None, 'HW3')", repr(testobj))

    def test_url_reverse(self):
        """
        Test the url_reverse method
        """
        locator = CourseLocator(org="a", offering="fancy_course-id", branch="branch_1.2-3")
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
                                 org=None, offering=None, branch=None):
        """
        Checks the version, org, offering, and branch in testobj
        """
        self.assertEqual(testobj.version_guid, version_guid, msg)
        self.assertEqual(testobj.org, org, msg)
        self.assertEqual(testobj.offering, offering, msg)
        self.assertEqual(testobj.branch, branch, msg)

    def check_block_locn_fields(self, testobj, msg, version_guid=None,
                                org=None, offering=None, branch=None, block=None):
        """
        Does adds a block id check over and above the check_course_locn_fields tests
        """
        self.check_course_locn_fields(testobj, msg, version_guid, org, offering,
                                      branch)
        self.assertEqual(testobj.block_id, block)
