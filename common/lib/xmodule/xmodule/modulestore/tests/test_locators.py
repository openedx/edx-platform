'''
Created on Mar 14, 2013

@author: dmitchell
'''
from unittest import TestCase
from xmodule.modulestore.locator import CourseLocator, BlockLocator
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
        self.assertIsInstance(BlockLocator(), BlockLocator,
            'empty constructor')

        # url inits
        testurn = 'edx://org/course/category/name'
        self.assertRaises(InvalidLocationError, BlockLocator, testurn)
        testurn = 'unknown/versionid/blockid'
        self.assertRaises(InvalidLocationError, BlockLocator, testurn)

        testurn = 'cvx/versionid'
        testobj = BlockLocator(testurn)
        self.check_block_locn_fields(testobj, testurn, 'versionid')
        self.assertEqual(testobj, BlockLocator(testobj),
            'initialization from another instance')

        testurn = 'cvx/versionid/'
        testobj = BlockLocator(testurn)
        self.check_block_locn_fields(testobj, testurn, 'versionid')

        testurn = 'cvx/versionid/blockid'
        testobj = BlockLocator(testurn)
        self.check_block_locn_fields(testobj, testurn, 'versionid',
            block='blockid')

        testurn = 'cvx/versionid/blockid/extraneousstuff?including=args'
        testobj = BlockLocator(testurn)
        self.check_block_locn_fields(testobj, testurn, 'versionid',
            block='blockid')

        testurn = 'cvx://versionid/blockid'
        testobj = BlockLocator(testurn)
        self.check_block_locn_fields(testobj, testurn, 'versionid',
            block='blockid')

        testurn = 'crx/courseid/blockid'
        testobj = BlockLocator(testurn)
        self.check_block_locn_fields(testobj, testurn, course_id='courseid',
            block='blockid')

        testurn = 'crx/courseid@revision/blockid'
        testobj = BlockLocator(testurn)
        self.check_block_locn_fields(testobj, testurn, course_id='courseid',
            revision='revision', block='blockid')
        self.assertEqual(testobj, BlockLocator(testobj),
            'run initialization from another instance')

        # arg list inits
        testobj = BlockLocator(version_guid='versionid')
        self.check_block_locn_fields(testobj, 'versionid arg', 'versionid')

        testobj = BlockLocator(version_guid='versionid', block_id='myblock')
        self.check_block_locn_fields(testobj, 'versionid arg', 'versionid',
            block='myblock')

        testobj = BlockLocator(course_id='courseid')
        self.check_block_locn_fields(testobj, 'courseid arg',
            course_id='courseid')

        testobj = BlockLocator(course_id='courseid', revision='rev')
        self.check_block_locn_fields(testobj, 'rev arg',
            course_id='courseid',
            revision='rev')
        # ignores garbage
        testobj = BlockLocator(course_id='courseid', revision='rev',
            block_id='this_block', potato='spud')
        self.check_block_locn_fields(testobj, 'extra keyword arg',
            course_id='courseid', block='this_block', revision='rev')

        # url w/ keyword override
        testurn = 'crx/courseid@revision/blockid'
        testobj = BlockLocator(testurn, revision='rev')
        self.check_block_locn_fields(testobj, 'rev override',
            course_id='courseid', block='blockid',
            revision='rev')

        # dict init w/ keyword overwrites
        testobj = BlockLocator({"version_guid": 'versionid',
            'block_id': 'dictblock'})
        self.check_block_locn_fields(testobj, 'versionid dict', 'versionid',
            block='dictblock')

        testobj = BlockLocator({"course_id": 'courseid',
            'block_id': 'dictblock'})
        self.check_block_locn_fields(testobj, 'courseid dict',
            block='dictblock', course_id='courseid')

        testobj = BlockLocator({"course_id": 'courseid', "revision": 'rev',
            'block_id': 'dictblock'})
        self.check_block_locn_fields(testobj, 'rev dict',
            course_id='courseid', block='dictblock',
            revision='rev')
        # ignores garbage
        testobj = BlockLocator({"course_id": 'courseid', "revision": 'rev',
            'block_id': 'dictblock', "potato": 'spud'})
        self.check_block_locn_fields(testobj, 'extra keyword dict',
            course_id='courseid', block='dictblock',
            revision='rev')
        testobj = BlockLocator({"course_id": 'courseid', "revision": 'rev',
            'block_id': 'dictblock'}, revision='alt', block_id='anotherblock')
        self.check_block_locn_fields(testobj, 'rev dict',
            course_id='courseid', block='anotherblock',
            revision='alt')

        # urn init w/ dict & keyword overwrites
        testobj = BlockLocator('crx/notcourse@notthis/northis',
            {"course_id": 'courseid'}, revision='alt', block_id='anotherblock')
        self.check_block_locn_fields(testobj, 'rev dict',
            course_id='courseid', block='anotherblock',
            revision='alt')

    def test_ensure_fully_specd(self):
        '''
        Test constructor and property accessors.
        '''
        self.assertRaises(InsufficientSpecificationError,
            BlockLocator.ensure_fully_specified, BlockLocator())

        # url inits
        testurn = 'edx://org/course/category/name'
        self.assertRaises(InvalidLocationError,
            BlockLocator.ensure_fully_specified, testurn)
        testurn = 'unknown/versionid/blockid'
        self.assertRaises(InvalidLocationError,
            BlockLocator.ensure_fully_specified, testurn)

        testurn = 'cvx/versionid'
        self.assertRaises(InsufficientSpecificationError,
            BlockLocator.ensure_fully_specified, testurn)

        testurn = 'cvx/versionid/'
        self.assertRaises(InsufficientSpecificationError,
            BlockLocator.ensure_fully_specified, testurn)

        testurn = 'cvx/versionid/blockid'
        self.assertIsInstance(BlockLocator.ensure_fully_specified(testurn),
            BlockLocator, testurn)

        testurn = 'cvx/versionid/blockid/extraneousstuff?including=args'
        self.assertIsInstance(BlockLocator.ensure_fully_specified(testurn),
            BlockLocator, testurn)

        testurn = 'cvx://versionid/blockid'
        self.assertIsInstance(BlockLocator.ensure_fully_specified(testurn),
            BlockLocator, testurn)

        testurn = 'crx/courseid/blockid'
        self.assertIsInstance(BlockLocator.ensure_fully_specified(testurn),
            BlockLocator, testurn)

        testurn = 'crx/courseid@revision/blockid'
        self.assertIsInstance(BlockLocator.ensure_fully_specified(testurn),
            BlockLocator, testurn)

        # arg list inits
        testobj = BlockLocator(version_guid='versionid')
        self.assertRaises(InsufficientSpecificationError,
            BlockLocator.ensure_fully_specified, testobj)

        testobj = BlockLocator(version_guid='versionid', block_id='myblock')
        self.assertIsInstance(BlockLocator.ensure_fully_specified(testurn),
            BlockLocator, testurn)

        testobj = BlockLocator(course_id='courseid')
        self.assertRaises(InsufficientSpecificationError,
            BlockLocator.ensure_fully_specified, testobj)

        testobj = BlockLocator(course_id='courseid', revision='rev')
        self.assertRaises(InsufficientSpecificationError,
            BlockLocator.ensure_fully_specified, testobj)

        testobj = BlockLocator(course_id='courseid', revision='rev',
            block_id='this_block')
        self.assertIsInstance(BlockLocator.ensure_fully_specified(testurn),
            BlockLocator, testurn)

    def check_course_locn_fields(self, testobj, msg, version_guid=None,
            course_id=None, revision=None):
        self.assertEqual(testobj.version_guid, version_guid, msg)
        self.assertEqual(testobj.course_id, course_id, msg)
        self.assertEqual(testobj.revision, revision, msg)

    def check_block_locn_fields(self, testobj, msg, version_guid=None,
            course_id=None, revision=None, block=None):
        self.check_course_locn_fields(testobj, msg, version_guid, course_id,
            revision)
        self.assertEqual(testobj.block_id, block, msg)
