'''
Created on Mar 14, 2013

@author: dmitchell
'''
from unittest import TestCase
from nose.plugins.skip import SkipTest

from bson.objectid import ObjectId
from xmodule.modulestore.locator import Locator, CourseLocator, BlockUsageLocator
from xmodule.modulestore.exceptions import InvalidLocationError, \
    InsufficientSpecificationError, OverSpecificationError


class LocatorTest(TestCase):

    def test_cant_instantiate_abstract_class(self):
        self.assertRaises(TypeError, Locator)

    def test_course_constructor_overspecified(self):
        self.assertRaises(
            OverSpecificationError,
            CourseLocator,
            url='edx://edu.mit.eecs.6002x',
            course_id='edu.harvard.history',
            revision='published',
            version_guid=ObjectId())
        self.assertRaises(
            OverSpecificationError,
            CourseLocator,
            url='edx://edu.mit.eecs.6002x',
            course_id='edu.harvard.history',
            version_guid=ObjectId())
        self.assertRaises(
            OverSpecificationError,
            CourseLocator,
            url='edx://edu.mit.eecs.6002x;published',
            revision='draft')
        self.assertRaises(
            OverSpecificationError,
            CourseLocator,
            course_id='edu.mit.eecs.6002x;published',
            revision='draft')

    def test_course_constructor_underspecified(self):
        self.assertRaises(InsufficientSpecificationError, CourseLocator)
        self.assertRaises(InsufficientSpecificationError, CourseLocator, revision='published')

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
        for bad_id in ('edu.mit.',
                       ' edu.mit.eecs',
                       'edu.mit.eecs ',
                       '@edu.mit.eecs',
                       '#edu.mit.eecs',
                       'edu.mit.ee cs',
                       'edu.mit.ee,cs',
                       'edu.mit.ee/cs',
                       'edu.mit.ee$cs',
                       'edu.mit.ee&cs',
                       'edu.mit.ee()cs',
                       ';this',
                       'edu.mit.eecs;',
                       'edu.mit.eecs;this;that',
                       'edu.mit.eecs;this;',
                       'edu.mit.eecs;this ',
                       'edu.mit.eecs;th%is ',
                       ):
            self.assertRaises(AssertionError, CourseLocator, course_id=bad_id)
            self.assertRaises(AssertionError, CourseLocator, url='edx://' + bad_id)

    def test_course_constructor_bad_url(self):
        for bad_url in ('edx://',
                        'edx:/edu.mit.eecs',
                        'http://edu.mit.eecs',
                        'edu.mit.eecs',
                        'edx//edu.mit.eecs'):
            self.assertRaises(AssertionError, CourseLocator, url=bad_url)

    def test_course_constructor_redundant_001(self):
        testurn = 'edu.mit.eecs.6002x'
        testobj = CourseLocator(course_id=testurn, url='edx://' + testurn)
        self.check_course_locn_fields(testobj, 'course_id', course_id=testurn)

    def test_course_constructor_redundant_002(self):
        testurn = 'edu.mit.eecs.6002x;published'
        expected_urn = 'edu.mit.eecs.6002x'
        expected_rev = 'published'
        testobj = CourseLocator(course_id=testurn, url='edx://' + testurn)
        self.check_course_locn_fields(testobj, 'course_id',
                                      course_id=expected_urn,
                                      revision=expected_rev)

    def test_course_constructor_course_id_no_revision(self):
        testurn = 'edu.mit.eecs.6002x'
        testobj = CourseLocator(course_id=testurn)
        self.check_course_locn_fields(testobj, 'course_id', course_id=testurn)
        self.assertEqual(testobj.course_id, testurn)
        self.assertEqual(str(testobj), testurn)
        self.assertEqual(testobj.url(), 'edx://' + testurn)

    def test_course_constructor_course_id_with_revision(self):
        testurn = 'edu.mit.eecs.6002x;published'
        expected_id = 'edu.mit.eecs.6002x'
        expected_revision = 'published'
        testobj = CourseLocator(course_id=testurn)
        self.check_course_locn_fields(testobj, 'course_id with revision',
                                      course_id=expected_id,
                                      revision=expected_revision,
                                      )
        self.assertEqual(testobj.course_id, expected_id)
        self.assertEqual(testobj.revision, expected_revision)
        self.assertEqual(str(testobj), testurn)
        self.assertEqual(testobj.url(), 'edx://' + testurn)

    def test_course_constructor_course_id_separate_revision(self):
        test_id = 'edu.mit.eecs.6002x'
        test_revision = 'published'
        expected_urn = 'edu.mit.eecs.6002x;published'
        testobj = CourseLocator(course_id=test_id, revision=test_revision)
        self.check_course_locn_fields(testobj, 'course_id with separate revision',
                                      course_id=test_id,
                                      revision=test_revision,
                                      )
        self.assertEqual(testobj.course_id, test_id)
        self.assertEqual(testobj.revision, test_revision)
        self.assertEqual(str(testobj), expected_urn)
        self.assertEqual(testobj.url(), 'edx://' + expected_urn)

    def test_course_constructor_course_id_repeated_revision(self):
        """
        The same revision appears in the course_id and the revision field.
        """
        test_id = 'edu.mit.eecs.6002x;published'
        test_revision = 'published'
        expected_id = 'edu.mit.eecs.6002x'
        expected_urn = 'edu.mit.eecs.6002x;published'
        testobj = CourseLocator(course_id=test_id, revision=test_revision)
        self.check_course_locn_fields(testobj, 'course_id with repeated revision',
                                      course_id=expected_id,
                                      revision=test_revision,
                                      )
        self.assertEqual(testobj.course_id, expected_id)
        self.assertEqual(testobj.revision, test_revision)
        self.assertEqual(str(testobj), expected_urn)
        self.assertEqual(testobj.url(), 'edx://' + expected_urn)

    def test_block_constructor(self):
        testurn = 'edu.mit.eecs.6002x;published#HW3'
        expected_id = 'edu.mit.eecs.6002x'
        expected_revision = 'published'
        expected_block_ref = 'HW3'
        testobj = BlockUsageLocator(course_id=testurn)
        self.check_block_locn_fields(testobj, 'test_block constructor',
                                     course_id=expected_id,
                                     revision=expected_revision,
                                     block=expected_block_ref)
        self.assertEqual(str(testobj), testurn)
        self.assertEqual(testobj.url(), 'edx://' + testurn)

    # ------------------------------------------------------------
    # Disabled tests

    def test_course_urls(self):
        '''
        Test constructor and property accessors.
        '''
        raise SkipTest()
        self.assertRaises(TypeError, CourseLocator, 'empty constructor')

        # url inits
        testurn = 'edx://org/course/category/name'
        self.assertRaises(InvalidLocationError, CourseLocator, url=testurn)
        testurn = 'unknown/versionid/blockid'
        self.assertRaises(InvalidLocationError, CourseLocator, url=testurn)

        testurn = 'cvx/versionid'
        testobj = CourseLocator(testurn)
        self.check_course_locn_fields(testobj, testurn, 'versionid')
        self.assertEqual(testobj, CourseLocator(testobj),
                         'initialization from another instance')

        testurn = 'cvx/versionid/'
        testobj = CourseLocator(testurn)
        self.check_course_locn_fields(testobj, testurn, 'versionid')

        testurn = 'cvx/versionid/blockid'
        testobj = CourseLocator(testurn)
        self.check_course_locn_fields(testobj, testurn, 'versionid')

        testurn = 'cvx/versionid/blockid/extraneousstuff?including=args'
        testobj = CourseLocator(testurn)
        self.check_course_locn_fields(testobj, testurn, 'versionid')

        testurn = 'cvx://versionid/blockid'
        testobj = CourseLocator(testurn)
        self.check_course_locn_fields(testobj, testurn, 'versionid')

        testurn = 'crx/courseid/blockid'
        testobj = CourseLocator(testurn)
        self.check_course_locn_fields(testobj, testurn, course_id='courseid')

        testurn = 'crx/courseid@revision/blockid'
        testobj = CourseLocator(testurn)
        self.check_course_locn_fields(testobj, testurn, course_id='courseid',
                                      revision='revision')
        self.assertEqual(testobj, CourseLocator(testobj),
                         'run initialization from another instance')

    def test_course_keyword_setters(self):
        raise SkipTest()
        # arg list inits
        testobj = CourseLocator(version_guid='versionid')
        self.check_course_locn_fields(testobj, 'versionid arg', 'versionid')

        testobj = CourseLocator(course_id='courseid')
        self.check_course_locn_fields(testobj, 'courseid arg',
                                      course_id='courseid')

        testobj = CourseLocator(course_id='courseid', revision='rev')
        self.check_course_locn_fields(testobj, 'rev arg',
                                      course_id='courseid',
                                      revision='rev')
        # ignores garbage
        testobj = CourseLocator(course_id='courseid', revision='rev',
                                potato='spud')
        self.check_course_locn_fields(testobj, 'extra keyword arg',
                                      course_id='courseid',
                                      revision='rev')

        # url w/ keyword override
        testurn = 'crx/courseid@revision/blockid'
        testobj = CourseLocator(testurn, revision='rev')
        self.check_course_locn_fields(testobj, 'rev override',
                                      course_id='courseid',
                                      revision='rev')

    def test_course_dict(self):
        raise SkipTest()
        # dict init w/ keyword overwrites
        testobj = CourseLocator({"version_guid": 'versionid'})
        self.check_course_locn_fields(testobj, 'versionid dict', 'versionid')

        testobj = CourseLocator({"course_id": 'courseid'})
        self.check_course_locn_fields(testobj, 'courseid dict',
                                      course_id='courseid')

        testobj = CourseLocator({"course_id": 'courseid', "revision": 'rev'})
        self.check_course_locn_fields(testobj, 'rev dict',
                                      course_id='courseid',
                                      revision='rev')
        # ignores garbage
        testobj = CourseLocator({"course_id": 'courseid', "revision": 'rev',
                                 "potato": 'spud'})
        self.check_course_locn_fields(testobj, 'extra keyword dict',
                                      course_id='courseid',
                                      revision='rev')
        testobj = CourseLocator({"course_id": 'courseid', "revision": 'rev'},
                                revision='alt')
        self.check_course_locn_fields(testobj, 'rev dict',
                                      course_id='courseid',
                                      revision='alt')

        # urn init w/ dict & keyword overwrites
        testobj = CourseLocator('crx/notcourse@notthis',
                                {"course_id": 'courseid'},
                                revision='alt')
        self.check_course_locn_fields(testobj, 'rev dict',
                                      course_id='courseid',
                                      revision='alt')

    def test_url(self):
        '''
        Ensure CourseLocator generates expected urls.
        '''
        raise SkipTest()

        testobj = CourseLocator(version_guid='versionid')
        self.assertEqual(testobj.url(), 'cvx/versionid', 'versionid')
        self.assertEqual(testobj, CourseLocator(testobj.url()),
                         'versionid conversion through url')

        testobj = CourseLocator(course_id='courseid')
        self.assertEqual(testobj.url(), 'crx/courseid', 'courseid')
        self.assertEqual(testobj, CourseLocator(testobj.url()),
                         'courseid conversion through url')

        testobj = CourseLocator(course_id='courseid', revision='rev')
        self.assertEqual(testobj.url(), 'crx/courseid@rev', 'rev')
        self.assertEqual(testobj, CourseLocator(testobj.url()),
                         'rev conversion through url')

    def test_html(self):
        '''
        Ensure CourseLocator generates expected urls.
        '''
        raise SkipTest()
        testobj = CourseLocator(version_guid='versionid')
        self.assertEqual(testobj.html_id(), 'cvx/versionid', 'versionid')
        self.assertEqual(testobj, CourseLocator(testobj.html_id()),
                         'versionid conversion through html_id')

        testobj = CourseLocator(course_id='courseid')
        self.assertEqual(testobj.html_id(), 'crx/courseid', 'courseid')
        self.assertEqual(testobj, CourseLocator(testobj.html_id()),
                         'courseid conversion through html_id')

        testobj = CourseLocator(course_id='courseid', revision='rev')
        self.assertEqual(testobj.html_id(), 'crx/courseid%40rev', 'rev')
        self.assertEqual(testobj, CourseLocator(testobj.html_id()),
                         'rev conversion through html_id')

    def test_block_locator(self):
        '''
        Test constructor and property accessors.
        '''
        raise SkipTest()
        self.assertIsInstance(BlockUsageLocator(), BlockUsageLocator,
                              'empty constructor')

        # url inits
        testurn = 'edx://org/course/category/name'
        self.assertRaises(InvalidLocationError, BlockUsageLocator, testurn)
        testurn = 'unknown/versionid/blockid'
        self.assertRaises(InvalidLocationError, BlockUsageLocator, testurn)

        testurn = 'cvx/versionid'
        testobj = BlockUsageLocator(testurn)
        self.check_block_locn_fields(testobj, testurn, 'versionid')
        self.assertEqual(testobj, BlockUsageLocator(testobj),
                         'initialization from another instance')

        testurn = 'cvx/versionid/'
        testobj = BlockUsageLocator(testurn)
        self.check_block_locn_fields(testobj, testurn, 'versionid')

        testurn = 'cvx/versionid/blockid'
        testobj = BlockUsageLocator(testurn)
        self.check_block_locn_fields(testobj, testurn, 'versionid',
                                     block='blockid')

        testurn = 'cvx/versionid/blockid/extraneousstuff?including=args'
        testobj = BlockUsageLocator(testurn)
        self.check_block_locn_fields(testobj, testurn, 'versionid',
                                     block='blockid')

        testurn = 'cvx://versionid/blockid'
        testobj = BlockUsageLocator(testurn)
        self.check_block_locn_fields(testobj, testurn, 'versionid',
                                     block='blockid')

        testurn = 'crx/courseid/blockid'
        testobj = BlockUsageLocator(testurn)
        self.check_block_locn_fields(testobj, testurn, course_id='courseid',
                                     block='blockid')

        testurn = 'crx/courseid@revision/blockid'
        testobj = BlockUsageLocator(testurn)
        self.check_block_locn_fields(testobj, testurn, course_id='courseid',
                                     revision='revision', block='blockid')
        self.assertEqual(testobj, BlockUsageLocator(testobj),
                         'run initialization from another instance')

    def test_block_keyword_init(self):
        # arg list inits
        raise SkipTest()
        testobj = BlockUsageLocator(version_guid='versionid')
        self.check_block_locn_fields(testobj, 'versionid arg', 'versionid')

        testobj = BlockUsageLocator(version_guid='versionid', usage_id='myblock')
        self.check_block_locn_fields(testobj, 'versionid arg', 'versionid',
                                     block='myblock')

        testobj = BlockUsageLocator(course_id='courseid')
        self.check_block_locn_fields(testobj, 'courseid arg',
                                     course_id='courseid')

        testobj = BlockUsageLocator(course_id='courseid', revision='rev')
        self.check_block_locn_fields(testobj, 'rev arg',
                                     course_id='courseid',
                                     revision='rev')
        # ignores garbage
        testobj = BlockUsageLocator(course_id='courseid', revision='rev',
                                    usage_id='this_block', potato='spud')
        self.check_block_locn_fields(testobj, 'extra keyword arg',
                                     course_id='courseid', block='this_block', revision='rev')

        # url w/ keyword override
        testurn = 'crx/courseid@revision/blockid'
        testobj = BlockUsageLocator(testurn, revision='rev')
        self.check_block_locn_fields(testobj, 'rev override',
                                     course_id='courseid', block='blockid',
                                     revision='rev')

    def test_block_keywords(self):
        # dict init w/ keyword overwrites
        raise SkipTest()
        testobj = BlockUsageLocator({"version_guid": 'versionid',
                                     'usage_id': 'dictblock'})
        self.check_block_locn_fields(testobj, 'versionid dict', 'versionid',
                                     block='dictblock')

        testobj = BlockUsageLocator({"course_id": 'courseid',
                                     'usage_id': 'dictblock'})
        self.check_block_locn_fields(testobj, 'courseid dict',
                                     block='dictblock', course_id='courseid')

        testobj = BlockUsageLocator({"course_id": 'courseid', "revision": 'rev',
                                     'usage_id': 'dictblock'})
        self.check_block_locn_fields(testobj, 'rev dict',
                                     course_id='courseid', block='dictblock',
                                     revision='rev')
        # ignores garbage
        testobj = BlockUsageLocator({"course_id": 'courseid', "revision": 'rev',
                                     'usage_id': 'dictblock', "potato": 'spud'})
        self.check_block_locn_fields(testobj, 'extra keyword dict',
                                     course_id='courseid', block='dictblock',
                                     revision='rev')
        testobj = BlockUsageLocator({"course_id": 'courseid', "revision": 'rev',
                                     'usage_id': 'dictblock'}, revision='alt', usage_id='anotherblock')
        self.check_block_locn_fields(testobj, 'rev dict',
                                     course_id='courseid', block='anotherblock',
                                     revision='alt')

        # urn init w/ dict & keyword overwrites
        testobj = BlockUsageLocator('crx/notcourse@notthis/northis',
                                    {"course_id": 'courseid'}, revision='alt', usage_id='anotherblock')
        self.check_block_locn_fields(testobj, 'rev dict',
                                     course_id='courseid', block='anotherblock',
                                     revision='alt')

    def test_ensure_fully_specd(self):
        '''
        Test constructor and property accessors.
        '''
        raise SkipTest()
        self.assertRaises(InsufficientSpecificationError,
                          BlockUsageLocator.ensure_fully_specified, BlockUsageLocator())

        # url inits
        testurn = 'edx://org/course/category/name'
        self.assertRaises(InvalidLocationError,
                          BlockUsageLocator.ensure_fully_specified, testurn)
        testurn = 'unknown/versionid/blockid'
        self.assertRaises(InvalidLocationError,
                          BlockUsageLocator.ensure_fully_specified, testurn)

        testurn = 'cvx/versionid'
        self.assertRaises(InsufficientSpecificationError,
                          BlockUsageLocator.ensure_fully_specified, testurn)

        testurn = 'cvx/versionid/'
        self.assertRaises(InsufficientSpecificationError,
                          BlockUsageLocator.ensure_fully_specified, testurn)

        testurn = 'cvx/versionid/blockid'
        self.assertIsInstance(BlockUsageLocator.ensure_fully_specified(testurn),
                              BlockUsageLocator, testurn)

        testurn = 'cvx/versionid/blockid/extraneousstuff?including=args'
        self.assertIsInstance(BlockUsageLocator.ensure_fully_specified(testurn),
                              BlockUsageLocator, testurn)

        testurn = 'cvx://versionid/blockid'
        self.assertIsInstance(BlockUsageLocator.ensure_fully_specified(testurn),
                              BlockUsageLocator, testurn)

        testurn = 'crx/courseid/blockid'
        self.assertIsInstance(BlockUsageLocator.ensure_fully_specified(testurn),
                              BlockUsageLocator, testurn)

        testurn = 'crx/courseid@revision/blockid'
        self.assertIsInstance(BlockUsageLocator.ensure_fully_specified(testurn),
                              BlockUsageLocator, testurn)

    def test_ensure_fully_via_keyword(self):
        # arg list inits
        raise SkipTest()
        testobj = BlockUsageLocator(version_guid='versionid')
        self.assertRaises(InsufficientSpecificationError,
                          BlockUsageLocator.ensure_fully_specified, testobj)

        testurn = 'crx/courseid@revision/blockid'
        testobj = BlockUsageLocator(version_guid='versionid', usage_id='myblock')
        self.assertIsInstance(BlockUsageLocator.ensure_fully_specified(testurn),
                              BlockUsageLocator, testurn)

        testobj = BlockUsageLocator(course_id='courseid')
        self.assertRaises(InsufficientSpecificationError,
                          BlockUsageLocator.ensure_fully_specified, testobj)

        testobj = BlockUsageLocator(course_id='courseid', revision='rev')
        self.assertRaises(InsufficientSpecificationError,
                          BlockUsageLocator.ensure_fully_specified, testobj)

        testobj = BlockUsageLocator(course_id='courseid', revision='rev',
                                    usage_id='this_block')
        self.assertIsInstance(BlockUsageLocator.ensure_fully_specified(testurn),
                              BlockUsageLocator, testurn)

    # ------------------------------------------------------------------
    # Utilities

    def check_course_locn_fields(self, testobj, msg, version_guid=None,
                                 course_id=None, revision=None):
        self.assertEqual(testobj.version_guid, version_guid, msg)
        self.assertEqual(testobj.course_id, course_id, msg)
        self.assertEqual(testobj.revision, revision, msg)

    def check_block_locn_fields(self, testobj, msg, version_guid=None,
                                course_id=None, revision=None, block=None):
        self.check_course_locn_fields(testobj, msg, version_guid, course_id,
                                      revision)
        self.assertEqual(testobj.usage_id, block)
