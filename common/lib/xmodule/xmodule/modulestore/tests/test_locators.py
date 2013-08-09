'''
Created on Mar 14, 2013

@author: dmitchell
'''
from unittest import TestCase

from bson.objectid import ObjectId
from xmodule.modulestore.locator import Locator, CourseLocator, BlockUsageLocator
from xmodule.modulestore.exceptions import InsufficientSpecificationError, OverSpecificationError


class LocatorTest(TestCase):

    def test_cant_instantiate_abstract_class(self):
        self.assertRaises(TypeError, Locator)

    def test_course_constructor_overspecified(self):
        self.assertRaises(
            OverSpecificationError,
            CourseLocator,
            url='edx://mit.eecs.6002x',
            course_id='harvard.history',
            branch='published',
            version_guid=ObjectId())
        self.assertRaises(
            OverSpecificationError,
            CourseLocator,
            url='edx://mit.eecs.6002x',
            course_id='harvard.history',
            version_guid=ObjectId())
        self.assertRaises(
            OverSpecificationError,
            CourseLocator,
            url='edx://mit.eecs.6002x;published',
            branch='draft')
        self.assertRaises(
            OverSpecificationError,
            CourseLocator,
            course_id='mit.eecs.6002x;published',
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
        self.assertEqual(str(testobj_1), '@' + test_id_1_loc)
        self.assertEqual(testobj_1.url(), 'edx://@' + test_id_1_loc)

        # Test using a given string
        test_id_2_loc = '519665f6223ebd6980884f2b'
        test_id_2 = ObjectId(test_id_2_loc)
        testobj_2 = CourseLocator(version_guid=test_id_2)
        self.check_course_locn_fields(testobj_2, 'version_guid', version_guid=test_id_2)
        self.assertEqual(str(testobj_2.version_guid), test_id_2_loc)
        self.assertEqual(str(testobj_2), '@' + test_id_2_loc)
        self.assertEqual(testobj_2.url(), 'edx://@' + test_id_2_loc)

    def test_course_constructor_bad_course_id(self):
        """
        Test all sorts of badly-formed course_ids (and urls with those course_ids)
        """
        for bad_id in ('mit.',
                       ' mit.eecs',
                       'mit.eecs ',
                       '@mit.eecs',
                       '#mit.eecs',
                       'mit.ee cs',
                       'mit.ee,cs',
                       'mit.ee/cs',
                       'mit.ee$cs',
                       'mit.ee&cs',
                       'mit.ee()cs',
                       ';this',
                       'mit.eecs;',
                       'mit.eecs;this;that',
                       'mit.eecs;this;',
                       'mit.eecs;this ',
                       'mit.eecs;th%is ',
                       ):
            self.assertRaises(AssertionError, CourseLocator, course_id=bad_id)
            self.assertRaises(AssertionError, CourseLocator, url='edx://' + bad_id)

    def test_course_constructor_bad_url(self):
        for bad_url in ('edx://',
                        'edx:/mit.eecs',
                        'http://mit.eecs',
                        'mit.eecs',
                        'edx//mit.eecs'):
            self.assertRaises(AssertionError, CourseLocator, url=bad_url)

    def test_course_constructor_redundant_001(self):
        testurn = 'mit.eecs.6002x'
        testobj = CourseLocator(course_id=testurn, url='edx://' + testurn)
        self.check_course_locn_fields(testobj, 'course_id', course_id=testurn)

    def test_course_constructor_redundant_002(self):
        testurn = 'mit.eecs.6002x;published'
        expected_urn = 'mit.eecs.6002x'
        expected_rev = 'published'
        testobj = CourseLocator(course_id=testurn, url='edx://' + testurn)
        self.check_course_locn_fields(testobj, 'course_id',
                                      course_id=expected_urn,
                                      branch=expected_rev)

    def test_course_constructor_course_id_no_branch(self):
        testurn = 'mit.eecs.6002x'
        testobj = CourseLocator(course_id=testurn)
        self.check_course_locn_fields(testobj, 'course_id', course_id=testurn)
        self.assertEqual(testobj.course_id, testurn)
        self.assertEqual(str(testobj), testurn)
        self.assertEqual(testobj.url(), 'edx://' + testurn)

    def test_course_constructor_course_id_with_branch(self):
        testurn = 'mit.eecs.6002x;published'
        expected_id = 'mit.eecs.6002x'
        expected_branch = 'published'
        testobj = CourseLocator(course_id=testurn)
        self.check_course_locn_fields(testobj, 'course_id with branch',
                                      course_id=expected_id,
                                      branch=expected_branch,
                                      )
        self.assertEqual(testobj.course_id, expected_id)
        self.assertEqual(testobj.branch, expected_branch)
        self.assertEqual(str(testobj), testurn)
        self.assertEqual(testobj.url(), 'edx://' + testurn)

    def test_course_constructor_course_id_separate_branch(self):
        test_id = 'mit.eecs.6002x'
        test_branch = 'published'
        expected_urn = 'mit.eecs.6002x;published'
        testobj = CourseLocator(course_id=test_id, branch=test_branch)
        self.check_course_locn_fields(testobj, 'course_id with separate branch',
                                      course_id=test_id,
                                      branch=test_branch,
                                      )
        self.assertEqual(testobj.course_id, test_id)
        self.assertEqual(testobj.branch, test_branch)
        self.assertEqual(str(testobj), expected_urn)
        self.assertEqual(testobj.url(), 'edx://' + expected_urn)

    def test_course_constructor_course_id_repeated_branch(self):
        """
        The same branch appears in the course_id and the branch field.
        """
        test_id = 'mit.eecs.6002x;published'
        test_branch = 'published'
        expected_id = 'mit.eecs.6002x'
        expected_urn = 'mit.eecs.6002x;published'
        testobj = CourseLocator(course_id=test_id, branch=test_branch)
        self.check_course_locn_fields(testobj, 'course_id with repeated branch',
                                      course_id=expected_id,
                                      branch=test_branch,
                                      )
        self.assertEqual(testobj.course_id, expected_id)
        self.assertEqual(testobj.branch, test_branch)
        self.assertEqual(str(testobj), expected_urn)
        self.assertEqual(testobj.url(), 'edx://' + expected_urn)

    def test_block_constructor(self):
        testurn = 'mit.eecs.6002x;published#HW3'
        expected_id = 'mit.eecs.6002x'
        expected_branch = 'published'
        expected_block_ref = 'HW3'
        testobj = BlockUsageLocator(course_id=testurn)
        self.check_block_locn_fields(testobj, 'test_block constructor',
                                     course_id=expected_id,
                                     branch=expected_branch,
                                     block=expected_block_ref)
        self.assertEqual(str(testobj), testurn)
        self.assertEqual(testobj.url(), 'edx://' + testurn)


    # ------------------------------------------------------------------
    # Utilities

    def check_course_locn_fields(self, testobj, msg, version_guid=None,
                                 course_id=None, branch=None):
        self.assertEqual(testobj.version_guid, version_guid, msg)
        self.assertEqual(testobj.course_id, course_id, msg)
        self.assertEqual(testobj.branch, branch, msg)

    def check_block_locn_fields(self, testobj, msg, version_guid=None,
                                course_id=None, branch=None, block=None):
        self.check_course_locn_fields(testobj, msg, version_guid, course_id,
                                      branch)
        self.assertEqual(testobj.usage_id, block)
