'''
Created on Mar 25, 2013

@author: dmitchell
'''
import datetime
import subprocess
import unittest
import uuid
from importlib import import_module

from xblock.core import Scope
from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.exceptions import InsufficientSpecificationError, ItemNotFoundError, VersionConflictError
from xmodule.modulestore.locator import CourseLocator, BlockUsageLocator, VersionTree, DescriptionLocator
from pytz import UTC
from path import path
import re


class SplitModuleTest(unittest.TestCase):
    '''
    The base set of tests manually populates a db w/ courses which have
    versions. It creates unique collection names and removes them after all
    tests finish.
    '''
    # Snippet of what would be in the django settings envs file
    modulestore_options = {
        'default_class': 'xmodule.raw_module.RawDescriptor',
        'host': 'localhost',
        'db': 'test_xmodule',
        'collection': 'modulestore{0}'.format(uuid.uuid4().hex),
        'fs_root': '',
    }

    MODULESTORE = {
        'ENGINE': 'xmodule.modulestore.split_mongo.SplitMongoModuleStore',
        'OPTIONS': modulestore_options
    }

    # don't create django dependency; so, duplicates common.py in envs
    match = re.search(r'(.*?/common)(?:$|/)', path(__file__))
    COMMON_ROOT = match.group(1)

    modulestore = None

    # These version_guids correspond to values hard-coded in fixture files
    # used for these tests. The files live in mitx/fixtures/splitmongo_json/*

    GUID_D0 = "1d00000000000000dddd0000"  # v12345d
    GUID_D1 = "1d00000000000000dddd1111"  # v12345d1
    GUID_D2 = "1d00000000000000dddd2222"  # v23456d
    GUID_D3 = "1d00000000000000dddd3333"  # v12345d0
    GUID_D4 = "1d00000000000000dddd4444"  # v23456d0
    GUID_D5 = "1d00000000000000dddd5555"  # v345679d
    GUID_P = "1d00000000000000eeee0000"  # v23456p

    @staticmethod
    def bootstrapDB():
        '''
        Loads the initial data into the db ensuring the collection name is
        unique.
        '''
        collection_prefix = SplitModuleTest.MODULESTORE['OPTIONS']['collection'] + '.'
        dbname = SplitModuleTest.MODULESTORE['OPTIONS']['db']
        processes = [
            subprocess.Popen([
                'mongoimport', '-d', dbname, '-c',
                collection_prefix + collection, '--jsonArray',
                '--file',
                SplitModuleTest.COMMON_ROOT + '/test/data/splitmongo_json/' + collection + '.json'
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            for collection in ('active_versions', 'structures', 'definitions')]
        for p in processes:
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                print "Couldn't run mongoimport:"
                print stdout
                print stderr
                raise Exception("DB did not init correctly")

    @classmethod
    def tearDownClass(cls):
        collection_prefix = SplitModuleTest.MODULESTORE['OPTIONS']['collection'] + '.'
        if SplitModuleTest.modulestore:
            for collection in ('active_versions', 'structures', 'definitions'):
                modulestore().db.drop_collection(collection_prefix + collection)
            # drop the modulestore to force re init
            SplitModuleTest.modulestore = None

    def findByIdInResult(self, collection, _id):
        """
        Result is a collection of descriptors. Find the one whose block id
        matches the _id.
        """
        for element in collection:
            if element.location.usage_id == _id:
                return element


class SplitModuleCourseTests(SplitModuleTest):
    '''
    Course CRUD operation tests
    '''

    def test_get_courses(self):
        courses = modulestore().get_courses('draft')
        # should have gotten 3 draft courses
        self.assertEqual(len(courses), 3, "Wrong number of courses")
        # check metadata -- NOTE no promised order
        course = self.findByIdInResult(courses, "head12345")
        self.assertEqual(course.location.course_id, "GreekHero")
        self.assertEqual(
            str(course.location.version_guid), self.GUID_D0,
            "course version mismatch"
        )
        self.assertEqual(course.category, 'course', 'wrong category')
        self.assertEqual(len(course.tabs), 6, "wrong number of tabs")
        self.assertEqual(
            course.display_name, "The Ancient Greek Hero",
            "wrong display name"
        )
        self.assertEqual(
            course.advertised_start, "Fall 2013",
            "advertised_start"
        )
        self.assertEqual(
            len(course.children), 3,
            "children")
        self.assertEqual(course.definition_locator.definition_id, "head12345_12")
        # check dates and graders--forces loading of descriptor
        self.assertEqual(course.edited_by, "testassist@edx.org")
        self.assertEqual(str(course.previous_version), self.GUID_D1)
        self.assertDictEqual(course.grade_cutoffs, {"Pass": 0.45})

    def test_revision_requests(self):
        # query w/ revision qualifier (both draft and published)
        courses_published = modulestore().get_courses('published')
        self.assertEqual(len(courses_published), 1, len(courses_published))
        course = self.findByIdInResult(courses_published, "head23456")
        self.assertIsNotNone(course, "published courses")
        self.assertEqual(course.location.course_id, "wonderful")
        self.assertEqual(str(course.location.version_guid), self.GUID_P,
                         course.location.version_guid)
        self.assertEqual(course.category, 'course', 'wrong category')
        self.assertEqual(len(course.tabs), 4, "wrong number of tabs")
        self.assertEqual(course.display_name, "The most wonderful course",
                         course.display_name)
        self.assertIsNone(course.advertised_start)
        self.assertEqual(len(course.children), 0,
                         "children")

    def test_search_qualifiers(self):
        # query w/ search criteria
        courses = modulestore().get_courses('draft', qualifiers={'org': 'testx'})
        self.assertEqual(len(courses), 2)
        self.assertIsNotNone(self.findByIdInResult(courses, "head12345"))
        self.assertIsNotNone(self.findByIdInResult(courses, "head23456"))

        courses = modulestore().get_courses(
            'draft',
            qualifiers={'edited_on': {"$lt": datetime.datetime(2013, 3, 28, 15)}})
        self.assertEqual(len(courses), 2)

        courses = modulestore().get_courses(
            'draft',
            qualifiers={'org': 'testx', "prettyid": "test_course"})
        self.assertEqual(len(courses), 1)
        self.assertIsNotNone(self.findByIdInResult(courses, "head12345"))

    def test_get_course(self):
        '''
        Test the various calling forms for get_course
        '''
        locator = CourseLocator(version_guid=self.GUID_D1)
        course = modulestore().get_course(locator)
        self.assertIsNone(course.location.course_id)
        self.assertEqual(str(course.location.version_guid), self.GUID_D1)
        self.assertEqual(course.category, 'course')
        self.assertEqual(len(course.tabs), 6)
        self.assertEqual(course.display_name, "The Ancient Greek Hero")
        self.assertIsNone(course.advertised_start)
        self.assertEqual(len(course.children), 0)
        self.assertEqual(course.definition_locator.definition_id, "head12345_11")
        # check dates and graders--forces loading of descriptor
        self.assertEqual(course.edited_by, "testassist@edx.org")
        self.assertDictEqual(course.grade_cutoffs, {"Pass": 0.55})

        locator = CourseLocator(course_id='GreekHero', revision='draft')
        course = modulestore().get_course(locator)
        self.assertEqual(course.location.course_id, "GreekHero")
        self.assertEqual(str(course.location.version_guid), self.GUID_D0)
        self.assertEqual(course.category, 'course')
        self.assertEqual(len(course.tabs), 6)
        self.assertEqual(course.display_name, "The Ancient Greek Hero")
        self.assertEqual(course.advertised_start, "Fall 2013")
        self.assertEqual(len(course.children), 3)
        # check dates and graders--forces loading of descriptor
        self.assertEqual(course.edited_by, "testassist@edx.org")
        self.assertDictEqual(course.grade_cutoffs, {"Pass": 0.45})

        locator = CourseLocator(course_id='wonderful', revision='published')
        course = modulestore().get_course(locator)
        self.assertEqual(course.location.course_id, "wonderful")
        self.assertEqual(str(course.location.version_guid), self.GUID_P)

        locator = CourseLocator(course_id='wonderful', revision='draft')
        course = modulestore().get_course(locator)
        self.assertEqual(str(course.location.version_guid), self.GUID_D2)

    def test_get_course_negative(self):
        # Now negative testing
        self.assertRaises(InsufficientSpecificationError,
                          modulestore().get_course, CourseLocator(course_id='edu.meh.blah'))
        self.assertRaises(ItemNotFoundError,
                          modulestore().get_course, CourseLocator(course_id='nosuchthing', revision='draft'))
        self.assertRaises(ItemNotFoundError,
                          modulestore().get_course,
                          CourseLocator(course_id='GreekHero', revision='published'))

    def test_course_successors(self):
        """
        get_course_successors(course_locator, version_history_depth=1)
        """
        locator = CourseLocator(version_guid=self.GUID_D3)
        result = modulestore().get_course_successors(locator)
        self.assertIsInstance(result, VersionTree)
        self.assertIsNone(result.locator.course_id)
        self.assertEqual(str(result.locator.version_guid), self.GUID_D3)
        self.assertEqual(len(result.children), 1)
        self.assertEqual(str(result.children[0].locator.version_guid), self.GUID_D1)
        self.assertEqual(len(result.children[0].children), 0, "descended more than one level")
        result = modulestore().get_course_successors(locator, version_history_depth=2)
        self.assertEqual(len(result.children), 1)
        self.assertEqual(str(result.children[0].locator.version_guid), self.GUID_D1)
        self.assertEqual(len(result.children[0].children), 1)
        result = modulestore().get_course_successors(locator, version_history_depth=99)
        self.assertEqual(len(result.children), 1)
        self.assertEqual(str(result.children[0].locator.version_guid), self.GUID_D1)
        self.assertEqual(len(result.children[0].children), 1)


class SplitModuleItemTests(SplitModuleTest):
    '''
    Item read tests including inheritance
    '''

    def test_has_item(self):
        '''
        has_item(BlockUsageLocator)
        '''
        # positive tests of various forms
        locator = BlockUsageLocator(version_guid=self.GUID_D1, usage_id='head12345')
        self.assertTrue(modulestore().has_item(locator),
                        "couldn't find in %s" % self.GUID_D1)

        locator = BlockUsageLocator(course_id='GreekHero', usage_id='head12345', revision='draft')
        self.assertTrue(
            modulestore().has_item(locator),
            "couldn't find in 12345"
        )
        self.assertTrue(
            modulestore().has_item(BlockUsageLocator(
                course_id=locator.course_id,
                revision='draft',
                usage_id=locator.usage_id
            )),
            "couldn't find in draft 12345"
        )
        self.assertFalse(
            modulestore().has_item(BlockUsageLocator(
                course_id=locator.course_id,
                revision='published',
                usage_id=locator.usage_id)),
            "found in published 12345"
        )
        locator.revision = 'draft'
        self.assertTrue(
            modulestore().has_item(locator),
            "not found in draft 12345"
        )

        # not a course obj
        locator = BlockUsageLocator(course_id='GreekHero', usage_id='chapter1', revision='draft')
        self.assertTrue(
            modulestore().has_item(locator),
            "couldn't find chapter1"
        )

        # in published course
        locator = BlockUsageLocator(course_id="wonderful", usage_id="head23456", revision='draft')
        self.assertTrue(modulestore().has_item(BlockUsageLocator(course_id=locator.course_id,
                                                                 usage_id=locator.usage_id,
                                                                 revision='published')),
                        "couldn't find in 23456")
        locator.revision = 'published'
        self.assertTrue(modulestore().has_item(locator), "couldn't find in 23456")

    def test_negative_has_item(self):
        # negative tests--not found
        # no such course or block
        locator = BlockUsageLocator(course_id="doesnotexist", usage_id="head23456", revision='draft')
        self.assertFalse(modulestore().has_item(locator))
        locator = BlockUsageLocator(course_id="wonderful", usage_id="doesnotexist", revision='draft')
        self.assertFalse(modulestore().has_item(locator))

        # negative tests--insufficient specification
        self.assertRaises(InsufficientSpecificationError, BlockUsageLocator)
        self.assertRaises(InsufficientSpecificationError,
                          modulestore().has_item, BlockUsageLocator(version_guid=self.GUID_D1))
        self.assertRaises(InsufficientSpecificationError,
                          modulestore().has_item, BlockUsageLocator(course_id='GreekHero'))

    def test_get_item(self):
        '''
        get_item(blocklocator)
        '''
        # positive tests of various forms
        locator = BlockUsageLocator(version_guid=self.GUID_D1, usage_id='head12345')
        block = modulestore().get_item(locator)
        self.assertIsInstance(block, CourseDescriptor)

        locator = BlockUsageLocator(course_id='GreekHero', usage_id='head12345', revision='draft')
        block = modulestore().get_item(locator)
        self.assertEqual(block.location.course_id, "GreekHero")
        # look at this one in detail
        self.assertEqual(len(block.tabs), 6, "wrong number of tabs")
        self.assertEqual(block.display_name, "The Ancient Greek Hero")
        self.assertEqual(block.advertised_start, "Fall 2013")
        self.assertEqual(len(block.children), 3)
        self.assertEqual(block.definition_locator.definition_id, "head12345_12")
        # check dates and graders--forces loading of descriptor
        self.assertEqual(block.edited_by, "testassist@edx.org")
        self.assertDictEqual(
            block.grade_cutoffs, {"Pass": 0.45},
        )

        # try to look up other revisions
        self.assertRaises(ItemNotFoundError,
                          modulestore().get_item,
                          BlockUsageLocator(course_id=locator.as_course_locator(),
                                            usage_id=locator.usage_id,
                                            revision='published'))
        locator.revision = 'draft'
        self.assertIsInstance(
            modulestore().get_item(locator),
            CourseDescriptor
        )

    def test_get_non_root(self):
        # not a course obj
        locator = BlockUsageLocator(course_id='GreekHero', usage_id='chapter1', revision='draft')
        block = modulestore().get_item(locator)
        self.assertEqual(block.location.course_id, "GreekHero")
        self.assertEqual(block.category, 'chapter')
        self.assertEqual(block.definition_locator.definition_id, "chapter12345_1")
        self.assertEqual(block.display_name, "Hercules")
        self.assertEqual(block.edited_by, "testassist@edx.org")

        # in published course
        locator = BlockUsageLocator(course_id="wonderful", usage_id="head23456", revision='published')
        self.assertIsInstance(
            modulestore().get_item(locator),
            CourseDescriptor
        )

        # negative tests--not found
        # no such course or block
        locator = BlockUsageLocator(course_id="doesnotexist", usage_id="head23456", revision='draft')
        with self.assertRaises(ItemNotFoundError):
            modulestore().get_item(locator)
        locator = BlockUsageLocator(course_id="wonderful", usage_id="doesnotexist", revision='draft')
        with self.assertRaises(ItemNotFoundError):
            modulestore().get_item(locator)

        # negative tests--insufficient specification
        with self.assertRaises(InsufficientSpecificationError):
            modulestore().get_item(BlockUsageLocator(version_guid=self.GUID_D1))
        with self.assertRaises(InsufficientSpecificationError):
            modulestore().get_item(BlockUsageLocator(course_id='GreekHero', revision='draft'))

    # pylint: disable=W0212
    def test_matching(self):
        '''
        test the block and value matches help functions
        '''
        self.assertTrue(modulestore()._value_matches('help', 'help'))
        self.assertFalse(modulestore()._value_matches('help', 'Help'))
        self.assertTrue(modulestore()._value_matches(['distract', 'help', 'notme'], 'help'))
        self.assertFalse(modulestore()._value_matches(['distract', 'Help', 'notme'], 'help'))
        self.assertFalse(modulestore()._value_matches({'field': ['distract', 'Help', 'notme']}, {'field': 'help'}))
        self.assertFalse(modulestore()._value_matches(['distract', 'Help', 'notme'], {'field': 'help'}))
        self.assertTrue(modulestore()._value_matches(
            {'field': ['distract', 'help', 'notme'],
                'irrelevant': 2},
            {'field': 'help'}))
        self.assertTrue(modulestore()._value_matches('I need some help', {'$regex': 'help'}))
        self.assertTrue(modulestore()._value_matches(['I need some help', 'today'], {'$regex': 'help'}))
        self.assertFalse(modulestore()._value_matches('I need some help', {'$regex': 'Help'}))
        self.assertFalse(modulestore()._value_matches(['I need some help', 'today'], {'$regex': 'Help'}))

        self.assertTrue(modulestore()._block_matches({'a': 1, 'b': 2}, {'a': 1}))
        self.assertTrue(modulestore()._block_matches({'a': 1, 'b': 2}, {'c': None}))
        self.assertTrue(modulestore()._block_matches({'a': 1, 'b': 2}, {'a': 1, 'c': None}))
        self.assertFalse(modulestore()._block_matches({'a': 1, 'b': 2}, {'a': 2}))
        self.assertFalse(modulestore()._block_matches({'a': 1, 'b': 2}, {'c': 1}))
        self.assertFalse(modulestore()._block_matches({'a': 1, 'b': 2}, {'a': 1, 'c': 1}))

    def test_get_items(self):
        '''
        get_items(locator, qualifiers, [revision])
        '''
        locator = CourseLocator(version_guid=self.GUID_D0)
        # get all modules
        matches = modulestore().get_items(locator, {})
        self.assertEqual(len(matches), 6)
        matches = modulestore().get_items(locator, {'category': 'chapter'})
        self.assertEqual(len(matches), 3)
        matches = modulestore().get_items(locator, {'category': 'garbage'})
        self.assertEqual(len(matches), 0)
        matches = modulestore().get_items(
            locator,
            {
                'category': 'chapter',
                'metadata': {'display_name': {'$regex': 'Hera'}}
            }
        )
        self.assertEqual(len(matches), 2)

        matches = modulestore().get_items(locator, {'children': 'chapter2'})
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].location.usage_id, 'head12345')

    def test_get_parents(self):
        '''
        get_parent_locations(locator, [usage_id], [revision]): [BlockUsageLocator]
        '''
        locator = CourseLocator(course_id="GreekHero", revision='draft')
        parents = modulestore().get_parent_locations(locator, usage_id='chapter1')
        self.assertEqual(len(parents), 1)
        self.assertEqual(parents[0].usage_id, 'head12345')
        self.assertEqual(parents[0].course_id, "GreekHero")
        locator.usage_id = 'chapter2'
        parents = modulestore().get_parent_locations(locator)
        self.assertEqual(len(parents), 1)
        self.assertEqual(parents[0].usage_id, 'head12345')
        parents = modulestore().get_parent_locations(locator, usage_id='nosuchblock')
        self.assertEqual(len(parents), 0)

    def test_get_children(self):
        """
        Test the existing get_children method on xdescriptors
        """
        locator = BlockUsageLocator(course_id="GreekHero", usage_id="head12345", revision='draft')
        block = modulestore().get_item(locator)
        children = block.get_children()
        expected_ids = [
            "chapter1", "chapter2", "chapter3"
        ]
        for child in children:
            self.assertEqual(child.category, "chapter")
            self.assertIn(child.location.usage_id, expected_ids)
            expected_ids.remove(child.location.usage_id)
        self.assertEqual(len(expected_ids), 0)


class TestItemCrud(SplitModuleTest):
    """
    Test create update and delete of items
    """
    # TODO do I need to test this case which I believe won't work:
    #  1) fetch a course and some of its blocks
    #  2) do a series of CRUD operations on those previously fetched elements
    # The problem here will be that the version_guid of the items will be the version at time of fetch.
    # Each separate save will change the head version; so, the 2nd piecemeal change will flag the version
    # conflict. That is, if versions are v0..vn and start as v0 in initial fetch, the first CRUD op will
    # say it's changing an object from v0, splitMongo will process it and make the current head v1, the next
    # crud op will pass in its v0 element and splitMongo will flag the version conflict.
    # What I don't know is how realistic this test is and whether to wrap the modulestore with a higher level
    # transactional operation which manages the version change or make the threading cache reason out whether or
    # not the changes are independent and additive and thus non-conflicting.
    # A use case I expect is
    # (client) change this metadata
    # (server) done, here's the new info which, btw, updates the course version to v1
    # (client) add these children to this other node (which says it came from v0 or
    #          will the client have refreshed the version before doing the op?)
    # In this case, having a server side transactional model won't help b/c the bug is a long-transaction on the
    # on the client where it would be a mistake for the server to assume anything about client consistency. The best
    # the server could do would be to see if the parent's children changed at all since v0.

    def test_create_minimal_item(self):
        """
        create_item(course_or_parent_locator, category, user, definition_locator=None, new_def_data=None,
        metadata=None): new_desciptor
        """
        # grab link to course to ensure new versioning works
        locator = CourseLocator(course_id="GreekHero", revision='draft')
        premod_course = modulestore().get_course(locator)
        premod_time = datetime.datetime.now(UTC) - datetime.timedelta(seconds=1)
        # add minimal one w/o a parent
        category = 'sequential'
        new_module = modulestore().create_item(
            locator, category, 'user123',
            metadata={'display_name': 'new sequential'}
        )
        # check that course version changed and course's previous is the other one
        self.assertEqual(new_module.location.course_id, "GreekHero")
        self.assertNotEqual(new_module.location.version_guid, premod_course.location.version_guid)
        self.assertIsNone(locator.version_guid, "Version inadvertently filled in")
        current_course = modulestore().get_course(locator)
        self.assertEqual(new_module.location.version_guid, current_course.location.version_guid)

        history_info = modulestore().get_course_history_info(current_course.location)
        self.assertEqual(history_info['previous_version'], premod_course.location.version_guid)
        self.assertEqual(str(history_info['original_version']), self.GUID_D3)
        self.assertEqual(history_info['edited_by'], "user123")
        self.assertGreaterEqual(history_info['edited_on'], premod_time)
        self.assertLessEqual(history_info['edited_on'], datetime.datetime.now(UTC))
        # check block's info: category, definition_locator, and display_name
        self.assertEqual(new_module.category, 'sequential')
        self.assertIsNotNone(new_module.definition_locator)
        self.assertEqual(new_module.display_name, 'new sequential')
        # check that block does not exist in previous version
        locator = BlockUsageLocator(
            version_guid=premod_course.location.version_guid,
            usage_id=new_module.location.usage_id
        )
        self.assertRaises(ItemNotFoundError, modulestore().get_item, locator)

    def test_create_parented_item(self):
        """
        Test create_item w/ specifying the parent of the new item
        """
        locator = BlockUsageLocator(course_id="wonderful", usage_id="head23456", revision='draft')
        premod_course = modulestore().get_course(locator)
        category = 'chapter'
        new_module = modulestore().create_item(
            locator, category, 'user123',
            metadata={'display_name': 'new chapter'},
            definition_locator=DescriptionLocator("chapter12345_2")
        )
        # check that course version changed and course's previous is the other one
        self.assertNotEqual(new_module.location.version_guid, premod_course.location.version_guid)
        parent = modulestore().get_item(locator)
        self.assertIn(new_module.location.usage_id, parent.children)
        self.assertEqual(new_module.definition_locator.definition_id, "chapter12345_2")

    def test_unique_naming(self):
        """
        Check that 2 modules of same type get unique usage_ids. Also check that if creation provides
        a definition id and new def data that it branches the definition in the db.
        Actually, this tries to test all create_item features not tested above.
        """
        locator = BlockUsageLocator(course_id="contender", usage_id="head345679", revision='draft')
        category = 'problem'
        premod_time = datetime.datetime.now(UTC) - datetime.timedelta(seconds=1)
        new_payload = "<problem>empty</problem>"
        new_module = modulestore().create_item(
            locator, category, 'anotheruser',
            metadata={'display_name': 'problem 1'},
            new_def_data=new_payload
        )
        another_payload = "<problem>not empty</problem>"
        another_module = modulestore().create_item(
            locator, category, 'anotheruser',
            metadata={'display_name': 'problem 2'},
            definition_locator=DescriptionLocator("problem12345_3_1"),
            new_def_data=another_payload
        )
        # check that course version changed and course's previous is the other one
        parent = modulestore().get_item(locator)
        self.assertNotEqual(new_module.location.usage_id, another_module.location.usage_id)
        self.assertIn(new_module.location.usage_id, parent.children)
        self.assertIn(another_module.location.usage_id, parent.children)
        self.assertEqual(new_module.data, new_payload)
        self.assertEqual(another_module.data, another_payload)
        # check definition histories
        new_history = modulestore().get_definition_history_info(new_module.definition_locator)
        self.assertIsNone(new_history['previous_version'])
        self.assertEqual(new_history['original_version'], new_module.definition_locator.definition_id)
        self.assertEqual(new_history['edited_by'], "anotheruser")
        self.assertLessEqual(new_history['edited_on'], datetime.datetime.now(UTC))
        self.assertGreaterEqual(new_history['edited_on'], premod_time)
        another_history = modulestore().get_definition_history_info(another_module.definition_locator)
        self.assertEqual(another_history['previous_version'], 'problem12345_3_1')
    # TODO check that default fields are set

    def test_update_metadata(self):
        """
        test updating an items metadata ensuring the definition doesn't version but the course does if it should
        """
        locator = BlockUsageLocator(course_id="GreekHero", usage_id="problem3_2", revision='draft')
        problem = modulestore().get_item(locator)
        pre_def_id = problem.definition_locator.definition_id
        pre_version_guid = problem.location.version_guid
        self.assertIsNotNone(pre_def_id)
        self.assertIsNotNone(pre_version_guid)
        premod_time = datetime.datetime.now(UTC) - datetime.timedelta(seconds=1)
        self.assertNotEqual(problem.max_attempts, 4, "Invalidates rest of test")

        problem.max_attempts = 4
        updated_problem = modulestore().update_item(problem, 'changeMaven')
        # check that course version changed and course's previous is the other one
        self.assertEqual(updated_problem.definition_locator.definition_id, pre_def_id)
        self.assertNotEqual(updated_problem.location.version_guid, pre_version_guid)
        self.assertEqual(updated_problem.max_attempts, 4)
        # refetch to ensure original didn't change
        original_location = BlockUsageLocator(
            version_guid=pre_version_guid,
            usage_id=problem.location.usage_id
        )
        problem = modulestore().get_item(original_location)
        self.assertNotEqual(problem.max_attempts, 4, "original changed")

        current_course = modulestore().get_course(locator)
        self.assertEqual(updated_problem.location.version_guid, current_course.location.version_guid)

        history_info = modulestore().get_course_history_info(current_course.location)
        self.assertEqual(history_info['previous_version'], pre_version_guid)
        self.assertEqual(str(history_info['original_version']), self.GUID_D3)
        self.assertEqual(history_info['edited_by'], "changeMaven")
        self.assertGreaterEqual(history_info['edited_on'], premod_time)
        self.assertLessEqual(history_info['edited_on'], datetime.datetime.now(UTC))

    def test_update_children(self):
        """
        test updating an item's children ensuring the definition doesn't version but the course does if it should
        """
        locator = BlockUsageLocator(course_id="GreekHero", usage_id="chapter3", revision='draft')
        block = modulestore().get_item(locator)
        pre_def_id = block.definition_locator.definition_id
        pre_version_guid = block.location.version_guid

        # reorder children
        self.assertGreater(len(block.children), 0, "meaningless test")
        moved_child = block.children.pop()
        updated_problem = modulestore().update_item(block, 'childchanger')
        # check that course version changed and course's previous is the other one
        self.assertEqual(updated_problem.definition_locator.definition_id, pre_def_id)
        self.assertNotEqual(updated_problem.location.version_guid, pre_version_guid)
        self.assertEqual(updated_problem.children, block.children)
        self.assertNotIn(moved_child, updated_problem.children)
        locator.usage_id = "chapter1"
        other_block = modulestore().get_item(locator)
        other_block.children.append(moved_child)
        other_updated = modulestore().update_item(other_block, 'childchanger')
        self.assertIn(moved_child, other_updated.children)

    def test_update_definition(self):
        """
        test updating an item's definition: ensure it gets versioned as well as the course getting versioned
        """
        locator = BlockUsageLocator(course_id="GreekHero", usage_id="head12345", revision='draft')
        block = modulestore().get_item(locator)
        pre_def_id = block.definition_locator.definition_id
        pre_version_guid = block.location.version_guid

        block.grading_policy['GRADER'][0]['min_count'] = 13
        updated_block = modulestore().update_item(block, 'definition_changer')

        self.assertNotEqual(updated_block.definition_locator.definition_id, pre_def_id)
        self.assertNotEqual(updated_block.location.version_guid, pre_version_guid)
        self.assertEqual(updated_block.grading_policy['GRADER'][0]['min_count'], 13)

    def test_update_manifold(self):
        """
        Test updating metadata, children, and definition in a single call ensuring all the versioning occurs
        """
        # first add 2 children to the course for the update to manipulate
        locator = BlockUsageLocator(course_id="contender", usage_id="head345679", revision='draft')
        category = 'problem'
        new_payload = "<problem>empty</problem>"
        modulestore().create_item(
            locator, category, 'test_update_manifold',
            metadata={'display_name': 'problem 1'},
            new_def_data=new_payload
        )
        another_payload = "<problem>not empty</problem>"
        modulestore().create_item(
            locator, category, 'test_update_manifold',
            metadata={'display_name': 'problem 2'},
            definition_locator=DescriptionLocator("problem12345_3_1"),
            new_def_data=another_payload
        )
        # pylint: disable=W0212
        modulestore()._clear_cache()

        # now begin the test
        block = modulestore().get_item(locator)
        pre_def_id = block.definition_locator.definition_id
        pre_version_guid = block.location.version_guid

        self.assertNotEqual(block.grading_policy['GRADER'][0]['min_count'], 13)
        block.grading_policy['GRADER'][0]['min_count'] = 13
        block.children = block.children[1:] + [block.children[0]]
        block.advertised_start = "Soon"

        updated_block = modulestore().update_item(block, "test_update_manifold")
        self.assertNotEqual(updated_block.definition_locator.definition_id, pre_def_id)
        self.assertNotEqual(updated_block.location.version_guid, pre_version_guid)
        self.assertEqual(updated_block.grading_policy['GRADER'][0]['min_count'], 13)
        self.assertEqual(updated_block.children[0], block.children[0])
        self.assertEqual(updated_block.advertised_start, "Soon")

    def test_delete_item(self):
        course = self.create_course_for_deletion()
        self.assertRaises(ValueError,
                          modulestore().delete_item,
                          course.location,
                          'deleting_user')
        reusable_location = BlockUsageLocator(
            course_id=course.location.course_id,
            usage_id=course.location.usage_id,
            revision='draft')

        # delete a leaf
        problems = modulestore().get_items(reusable_location, {'category': 'problem'})
        locn_to_del = problems[0].location
        new_course_loc = modulestore().delete_item(locn_to_del, 'deleting_user')
        deleted = BlockUsageLocator(course_id=reusable_location.course_id,
                                    revision=reusable_location.revision,
                                    usage_id=locn_to_del.usage_id)
        self.assertFalse(modulestore().has_item(deleted))
        self.assertRaises(VersionConflictError, modulestore().has_item, locn_to_del)
        locator = BlockUsageLocator(
            version_guid=locn_to_del.version_guid,
            usage_id=locn_to_del.usage_id
        )
        self.assertTrue(modulestore().has_item(locator))
        self.assertNotEqual(new_course_loc.version_guid, course.location.version_guid)

        # delete a subtree
        nodes = modulestore().get_items(reusable_location, {'category': 'chapter'})
        new_course_loc = modulestore().delete_item(nodes[0].location, 'deleting_user')
        # check subtree

        def check_subtree(node):
            if node:
                node_loc = node.location
                self.assertFalse(modulestore().has_item(
                    BlockUsageLocator(
                        course_id=node_loc.course_id,
                        revision=node_loc.revision,
                        usage_id=node.location.usage_id)))
                locator = BlockUsageLocator(
                    version_guid=node.location.version_guid,
                    usage_id=node.location.usage_id)
                self.assertTrue(modulestore().has_item(locator))
                if node.has_children:
                    for sub in node.get_children():
                        check_subtree(sub)
        check_subtree(nodes[0])

    def create_course_for_deletion(self):
        course = modulestore().create_course('nihilx', 'deletion', 'deleting_user')
        root = BlockUsageLocator(
            course_id=course.location.course_id,
            usage_id=course.location.usage_id,
            revision='draft')
        for _ in range(4):
            self.create_subtree_for_deletion(root, ['chapter', 'vertical', 'problem'])
        return modulestore().get_item(root)

    def create_subtree_for_deletion(self, parent, category_queue):
        if not category_queue:
            return
        node = modulestore().create_item(parent, category_queue[0], 'deleting_user')
        node_loc = BlockUsageLocator(parent.as_course_locator(), usage_id=node.location.usage_id)
        for _ in range(4):
            self.create_subtree_for_deletion(node_loc, category_queue[1:])


class TestCourseCreation(SplitModuleTest):
    """
    Test create_course, duh :-)
    """
    def test_simple_creation(self):
        """
        The simplest case but probing all expected results from it.
        """
        # Oddly getting differences of 200nsec
        pre_time = datetime.datetime.now(UTC) - datetime.timedelta(milliseconds=1)
        new_course = modulestore().create_course('test_org', 'test_course', 'create_user')
        new_locator = new_course.location
        # check index entry
        index_info = modulestore().get_course_index_info(new_locator)
        self.assertEqual(index_info['org'], 'test_org')
        self.assertEqual(index_info['prettyid'], 'test_course')
        self.assertGreaterEqual(index_info["edited_on"], pre_time)
        self.assertLessEqual(index_info["edited_on"], datetime.datetime.now(UTC))
        self.assertEqual(index_info['edited_by'], 'create_user')
        # check structure info
        structure_info = modulestore().get_course_history_info(new_locator)
        self.assertEqual(structure_info['original_version'], index_info['versions']['draft'])
        self.assertIsNone(structure_info['previous_version'])
        self.assertGreaterEqual(structure_info["edited_on"], pre_time)
        self.assertLessEqual(structure_info["edited_on"], datetime.datetime.now(UTC))
        self.assertEqual(structure_info['edited_by'], 'create_user')
        # check the returned course object
        self.assertIsInstance(new_course, CourseDescriptor)
        self.assertEqual(new_course.category, 'course')
        self.assertFalse(new_course.show_calculator)
        self.assertTrue(new_course.allow_anonymous)
        self.assertEqual(len(new_course.children), 0)
        self.assertEqual(new_course.edited_by, "create_user")
        self.assertEqual(len(new_course.grading_policy['GRADER']), 4)
        self.assertDictEqual(new_course.grade_cutoffs, {"Pass": 0.5})

    def test_cloned_course(self):
        """
        Test making a course which points to an existing draft and published but not making any changes to either.
        """
        pre_time = datetime.datetime.now(UTC)
        original_locator = CourseLocator(course_id="wonderful", revision='draft')
        original_index = modulestore().get_course_index_info(original_locator)
        new_draft = modulestore().create_course(
            'leech', 'best_course', 'leech_master', id_root='best',
            versions_dict=original_index['versions'])
        new_draft_locator = new_draft.location
        self.assertRegexpMatches(new_draft_locator.course_id, r'best.*')
        # the edited_by and other meta fields on the new course will be the original author not this one
        self.assertEqual(new_draft.edited_by, 'test@edx.org')
        self.assertLess(new_draft.edited_on, pre_time)
        self.assertEqual(new_draft.location.version_guid, original_index['versions']['draft'])
        # however the edited_by and other meta fields on course_index will be this one
        new_index = modulestore().get_course_index_info(new_draft_locator)
        self.assertGreaterEqual(new_index["edited_on"], pre_time)
        self.assertLessEqual(new_index["edited_on"], datetime.datetime.now(UTC))
        self.assertEqual(new_index['edited_by'], 'leech_master')

        new_published_locator = CourseLocator(course_id=new_draft_locator.course_id, revision='published')
        new_published = modulestore().get_course(new_published_locator)
        self.assertEqual(new_published.edited_by, 'test@edx.org')
        self.assertLess(new_published.edited_on, pre_time)
        self.assertEqual(new_published.location.version_guid, original_index['versions']['published'])

        # changing this course will not change the original course
        # using new_draft.location will insert the chapter under the course root
        new_item = modulestore().create_item(
            new_draft.location, 'chapter', 'leech_master',
            metadata={'display_name': 'new chapter'}
        )
        new_draft_locator.version_guid = None
        new_index = modulestore().get_course_index_info(new_draft_locator)
        self.assertNotEqual(new_index['versions']['draft'], original_index['versions']['draft'])
        new_draft = modulestore().get_course(new_draft_locator)
        self.assertEqual(new_item.edited_by, 'leech_master')
        self.assertGreaterEqual(new_item.edited_on, pre_time)
        self.assertNotEqual(new_item.location.version_guid, original_index['versions']['draft'])
        self.assertNotEqual(new_draft.location.version_guid, original_index['versions']['draft'])
        structure_info = modulestore().get_course_history_info(new_draft_locator)
        self.assertGreaterEqual(structure_info["edited_on"], pre_time)
        self.assertLessEqual(structure_info["edited_on"], datetime.datetime.now(UTC))
        self.assertEqual(structure_info['edited_by'], 'leech_master')

        original_course = modulestore().get_course(original_locator)
        self.assertEqual(original_course.location.version_guid, original_index['versions']['draft'])
        self.assertFalse(
            modulestore().has_item(BlockUsageLocator(
                original_locator,
                usage_id=new_item.location.usage_id
            ))
        )

    def test_derived_course(self):
        """
        Create a new course which overrides metadata and course_data
        """
        pre_time = datetime.datetime.now(UTC)
        original_locator = CourseLocator(course_id="contender", revision='draft')
        original = modulestore().get_course(original_locator)
        original_index = modulestore().get_course_index_info(original_locator)
        data_payload = {}
        metadata_payload = {}
        for field in original.fields:
            if field.scope == Scope.content and field.name != 'location':
                data_payload[field.name] = getattr(original, field.name)
            elif field.scope == Scope.settings:
                metadata_payload[field.name] = getattr(original, field.name)
        data_payload['grading_policy']['GRADE_CUTOFFS'] = {'A': .9, 'B': .8, 'C': .65}
        metadata_payload['display_name'] = 'Derivative'
        new_draft = modulestore().create_course(
            'leech', 'derivative', 'leech_master', id_root='counter',
            versions_dict={'draft': original_index['versions']['draft']},
            course_data=data_payload,
            metadata=metadata_payload
        )
        new_draft_locator = new_draft.location
        self.assertRegexpMatches(new_draft_locator.course_id, r'counter.*')
        # the edited_by and other meta fields on the new course will be the original author not this one
        self.assertEqual(new_draft.edited_by, 'leech_master')
        self.assertGreaterEqual(new_draft.edited_on, pre_time)
        self.assertNotEqual(new_draft.location.version_guid, original_index['versions']['draft'])
        # however the edited_by and other meta fields on course_index will be this one
        new_index = modulestore().get_course_index_info(new_draft_locator)
        self.assertGreaterEqual(new_index["edited_on"], pre_time)
        self.assertLessEqual(new_index["edited_on"], datetime.datetime.now(UTC))
        self.assertEqual(new_index['edited_by'], 'leech_master')
        self.assertEqual(new_draft.display_name, metadata_payload['display_name'])
        self.assertDictEqual(
            new_draft.grading_policy['GRADE_CUTOFFS'],
            data_payload['grading_policy']['GRADE_CUTOFFS']
        )

    def test_update_course_index(self):
        """
        Test changing the org, pretty id, etc of a course. Test that it doesn't allow changing the id, etc.
        """
        locator = CourseLocator(course_id="GreekHero", revision='draft')
        modulestore().update_course_index(locator, {'org': 'funkyU'})
        course_info = modulestore().get_course_index_info(locator)
        self.assertEqual(course_info['org'], 'funkyU')

        modulestore().update_course_index(locator, {'org': 'moreFunky', 'prettyid': 'Ancient Greek Demagods'})
        course_info = modulestore().get_course_index_info(locator)
        self.assertEqual(course_info['org'], 'moreFunky')
        self.assertEqual(course_info['prettyid'], 'Ancient Greek Demagods')

        self.assertRaises(ValueError, modulestore().update_course_index, locator, {'_id': 'funkygreeks'})

        with self.assertRaises(ValueError):
            modulestore().update_course_index(
                locator,
                {'edited_on': datetime.datetime.now(UTC)}
            )
        with self.assertRaises(ValueError):
            modulestore().update_course_index(
                locator,
                {'edited_by': 'sneak'}
            )

        self.assertRaises(ValueError, modulestore().update_course_index, locator,
                          {'versions': {'draft': self.GUID_D1}})

        # an allowed but not necessarily recommended way to revert the draft version
        versions = course_info['versions']
        versions['draft'] = self.GUID_D1
        modulestore().update_course_index(locator, {'versions': versions}, update_versions=True)
        course = modulestore().get_course(locator)
        self.assertEqual(str(course.location.version_guid), self.GUID_D1)

        # an allowed but not recommended way to publish a course
        versions['published'] = self.GUID_D1
        modulestore().update_course_index(locator, {'versions': versions}, update_versions=True)
        course = modulestore().get_course(CourseLocator(course_id=locator.course_id, revision="published"))
        self.assertEqual(str(course.location.version_guid), self.GUID_D1)


class TestInheritance(SplitModuleTest):
    """
    Test the metadata inheritance mechanism.
    """
    def test_inheritance(self):
        """
        The actual test
        """
        # Note, not testing value where defined (course) b/c there's no
        # defined accessor for it on CourseDescriptor.
        locator = BlockUsageLocator(course_id="GreekHero", usage_id="problem3_2", revision='draft')
        node = modulestore().get_item(locator)
        # inherited
        self.assertEqual(node.graceperiod, datetime.timedelta(hours=2))
        locator = BlockUsageLocator(course_id="GreekHero", usage_id="problem1", revision='draft')
        node = modulestore().get_item(locator)
        # overridden
        self.assertEqual(node.graceperiod, datetime.timedelta(hours=4))

    # TODO test inheritance after set and delete of attrs


#===========================================
# This mocks the django.modulestore() function and is intended purely to disentangle
# the tests from django
def modulestore():
    def load_function(path):
        module_path, _, name = path.rpartition('.')
        return getattr(import_module(module_path), name)

    if SplitModuleTest.modulestore is None:
        SplitModuleTest.bootstrapDB()
        class_ = load_function(SplitModuleTest.MODULESTORE['ENGINE'])

        options = {}

        options.update(SplitModuleTest.MODULESTORE['OPTIONS'])
        options['render_template'] = render_to_template_mock

        # pylint: disable=W0142
        SplitModuleTest.modulestore = class_(**options)

    return SplitModuleTest.modulestore


# pylint: disable=W0613
def render_to_template_mock(*args):
    pass
