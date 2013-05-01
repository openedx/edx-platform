'''
Created on Mar 14, 2013

@author: dmitchell
'''
from unittest import TestCase
from xmodule.modulestore.locator import CourseLocator, BlockUsageLocator
from xmodule.modulestore.exceptions import InvalidLocationError, \
    InsufficientSpecificationError


class LocatorTest(TestCase):

    def test_course_locator(self):
        '''
        Test constructor and property accessors.
        '''
        self.assertIsInstance(CourseLocator(), CourseLocator,
            'empty constructor')

        # url inits
        testurn = 'edx://org/course/category/name'
        self.assertRaises(InvalidLocationError, CourseLocator, testurn)
        testurn = 'unknown/versionid/blockid'
        self.assertRaises(InvalidLocationError, CourseLocator, testurn)

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

        # arg list inits
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

        # dict init w/ keyword overwrites
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

        # arg list inits
        testobj = BlockUsageLocator(version_guid='versionid')
        self.assertRaises(InsufficientSpecificationError,
            BlockUsageLocator.ensure_fully_specified, testobj)

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
