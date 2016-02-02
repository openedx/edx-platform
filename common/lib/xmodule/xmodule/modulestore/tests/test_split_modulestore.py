"""
    Test split modulestore w/o using any django stuff.
"""
from mock import patch
import datetime
from importlib import import_module
from path import Path as path
import random
import re
import unittest
import uuid

import ddt
from contracts import contract
from nose.plugins.attrib import attr
from django.core.cache import caches, InvalidCacheBackendError

from openedx.core.lib import tempdir
from xblock.fields import Reference, ReferenceList, ReferenceValueDict
from xmodule.course_module import CourseDescriptor
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.exceptions import (
    ItemNotFoundError, VersionConflictError,
    DuplicateItemError, DuplicateCourseError,
    InsufficientSpecificationError
)
from opaque_keys.edx.locator import CourseKey, CourseLocator, BlockUsageLocator, VersionTree, LocalId
from ccx_keys.locator import CCXBlockUsageLocator
from xmodule.modulestore.inheritance import InheritanceMixin
from xmodule.x_module import XModuleMixin
from xmodule.fields import Date, Timedelta
from xmodule.modulestore.split_mongo.split import SplitMongoModuleStore
from xmodule.modulestore.tests.test_modulestore import check_has_course_method
from xmodule.modulestore.split_mongo import BlockKey
from xmodule.modulestore.tests.factories import check_mongo_calls
from xmodule.modulestore.tests.mongo_connection import MONGO_PORT_NUM, MONGO_HOST
from xmodule.modulestore.tests.utils import mock_tab_from_json
from xmodule.modulestore.edit_info import EditInfoMixin


BRANCH_NAME_DRAFT = ModuleStoreEnum.BranchName.draft
BRANCH_NAME_PUBLISHED = ModuleStoreEnum.BranchName.published


@attr('mongo')
class SplitModuleTest(unittest.TestCase):
    '''
    The base set of tests manually populates a db w/ courses which have
    versions. It creates unique collection names and removes them after all
    tests finish.
    '''
    # Snippets of what would be in the django settings envs file
    DOC_STORE_CONFIG = {
        'host': MONGO_HOST,
        'db': 'test_xmodule',
        'port': MONGO_PORT_NUM,
        'collection': 'modulestore{0}'.format(uuid.uuid4().hex[:5]),
    }
    modulestore_options = {
        'default_class': 'xmodule.raw_module.RawDescriptor',
        'fs_root': tempdir.mkdtemp_clean(),
        'xblock_mixins': (InheritanceMixin, XModuleMixin, EditInfoMixin)
    }

    MODULESTORE = {
        'ENGINE': 'xmodule.modulestore.split_mongo.split.SplitMongoModuleStore',
        'DOC_STORE_CONFIG': DOC_STORE_CONFIG,
        'OPTIONS': modulestore_options
    }

    # don't create django dependency; so, duplicates common.py in envs
    match = re.search(r'(.*?/common)(?:$|/)', path(__file__))
    COMMON_ROOT = match.group(1)

    modulestore = None

    _date_field = Date()
    _time_delta_field = Timedelta()
    COURSE_CONTENT = {
        "testx.GreekHero": {
            "org": "testx",
            "course": "GreekHero",
            "run": "run",
            "root_block_id": "head12345",
            "user_id": "test@edx.org",
            "fields": {
                "tabs": [
                    {
                        "type": "courseware"
                    },
                    {
                        "type": "course_info",
                        "name": "Course Info"
                    },
                    {
                        "type": "discussion",
                        "name": "Discussion"
                    },
                    {
                        "type": "wiki",
                        "name": "Wiki"
                    }
                ],
                "start": _date_field.from_json("2013-02-14T05:00"),
                "display_name": "The Ancient Greek Hero",
                "grading_policy": {
                    "GRADER": [
                        {
                            "min_count": 5,
                            "weight": 0.15,
                            "type": "Homework",
                            "drop_count": 1,
                            "short_label": "HWa"
                        },
                        {
                            "short_label": "",
                            "min_count": 2,
                            "type": "Lab",
                            "drop_count": 0,
                            "weight": 0.15
                        },
                        {
                            "short_label": "Midterm",
                            "min_count": 1,
                            "type": "Midterm Exam",
                            "drop_count": 0,
                            "weight": 0.3
                        },
                        {
                            "short_label": "Final",
                            "min_count": 1,
                            "type": "Final Exam",
                            "drop_count": 0,
                            "weight": 0.4
                        }
                    ],
                    "GRADE_CUTOFFS": {
                        "Pass": 0.75
                    },
                },
            },
            "revisions": [
                {
                    "user_id": "testassist@edx.org",
                    "update": {
                        ("course", "head12345"): {
                            "end": _date_field.from_json("2013-04-13T04:30"),
                            "tabs": [
                                {
                                    "type": "courseware"
                                },
                                {
                                    "type": "course_info",
                                    "name": "Course Info"
                                },
                                {
                                    "type": "discussion",
                                    "name": "Discussion"
                                },
                                {
                                    "type": "wiki",
                                    "name": "Wiki"
                                },
                                {
                                    "type": "static_tab",
                                    "name": "Syllabus",
                                    "url_slug": "01356a17b5924b17a04b7fc2426a3798"
                                },
                                {
                                    "type": "static_tab",
                                    "name": "Advice for Students",
                                    "url_slug": "57e9991c0d794ff58f7defae3e042e39"
                                }
                            ],
                            "graceperiod": _time_delta_field.from_json("2 hours 0 minutes 0 seconds"),
                            "grading_policy": {
                                "GRADER": [
                                    {
                                        "min_count": 5,
                                        "weight": 0.15,
                                        "type": "Homework",
                                        "drop_count": 1,
                                        "short_label": "HWa"
                                    },
                                    {
                                        "short_label": "",
                                        "min_count": 12,
                                        "type": "Lab",
                                        "drop_count": 2,
                                        "weight": 0.15
                                    },
                                    {
                                        "short_label": "Midterm",
                                        "min_count": 1,
                                        "type": "Midterm Exam",
                                        "drop_count": 0,
                                        "weight": 0.3
                                    },
                                    {
                                        "short_label": "Final",
                                        "min_count": 1,
                                        "type": "Final Exam",
                                        "drop_count": 0,
                                        "weight": 0.4
                                    }
                                ],
                                "GRADE_CUTOFFS": {
                                    "Pass": 0.55
                                }
                            },
                        }
                    }
                },
                {
                    "user_id": "testassist@edx.org",
                    "update": {
                        ("course", "head12345"): {
                            "end": _date_field.from_json("2013-06-13T04:30"),
                            "grading_policy": {
                                "GRADER": [
                                    {
                                        "min_count": 4,
                                        "weight": 0.15,
                                        "type": "Homework",
                                        "drop_count": 2,
                                        "short_label": "HWa"
                                    },
                                    {
                                        "short_label": "",
                                        "min_count": 12,
                                        "type": "Lab",
                                        "drop_count": 2,
                                        "weight": 0.15
                                    },
                                    {
                                        "short_label": "Midterm",
                                        "min_count": 1,
                                        "type": "Midterm Exam",
                                        "drop_count": 0,
                                        "weight": 0.3
                                    },
                                    {
                                        "short_label": "Final",
                                        "min_count": 1,
                                        "type": "Final Exam",
                                        "drop_count": 0,
                                        "weight": 0.4
                                    }
                                ],
                                "GRADE_CUTOFFS": {
                                    "Pass": 0.45
                                }
                            },
                            "enrollment_start": _date_field.from_json("2013-01-01T05:00"),
                            "enrollment_end": _date_field.from_json("2013-03-02T05:00"),
                            "advertised_start": "Fall 2013",
                        }
                    },
                    "create": [
                        {
                            "id": "chapter1",
                            "parent": "head12345",
                            "parent_type": "course",
                            "category": "chapter",
                            "fields": {
                                "display_name": "Hercules"
                            },
                        },
                        {
                            "id": "chapter2",
                            "parent": "head12345",
                            "parent_type": "course",
                            "category": "chapter",
                            "fields": {
                                "display_name": "Hera heckles Hercules"
                            },
                        },
                        {
                            "id": "chapter3",
                            "parent": "head12345",
                            "parent_type": "course",
                            "category": "chapter",
                            "fields": {
                                "display_name": "Hera cuckolds Zeus"
                            },
                        },
                        {
                            "id": "problem1",
                            "parent": "chapter3",
                            "parent_type": "chapter",
                            "category": "problem",
                            "fields": {
                                "display_name": "Problem 3.1",
                                "graceperiod": _time_delta_field.from_json("4 hours 0 minutes 0 seconds"),
                            },
                        },
                        {
                            "id": "problem3_2",
                            "parent": "chapter3",
                            "parent_type": "chapter",
                            "category": "problem",
                            "fields": {
                                "display_name": "Problem 3.2"
                            },
                        },
                        {
                            "id": "problem32",
                            "parent": "chapter3",
                            "parent_type": "chapter",
                            "category": "problem",
                            "fields": {
                                "display_name": "Problem 3.3",
                                "group_access": {"3": ["33"]},
                            },
                        }
                    ]
                },
            ]
        },
        "testx.wonderful": {
            "org": "testx",
            "course": "wonderful",
            "run": "run",
            "root_block_id": "head23456",
            "user_id": "test@edx.org",
            "fields": {
                "tabs": [
                    {
                        "type": "courseware"
                    },
                    {
                        "type": "course_info",
                        "name": "Course Info"
                    },
                    {
                        "type": "discussion",
                        "name": "Discussion"
                    },
                    {
                        "type": "wiki",
                        "name": "Wiki"
                    }
                ],
                "start": _date_field.from_json("2013-02-14T05:00"),
                "display_name": "A wonderful course",
                "grading_policy": {
                    "GRADER": [
                        {
                            "min_count": 14,
                            "weight": 0.25,
                            "type": "Homework",
                            "drop_count": 1,
                            "short_label": "HWa"
                        },
                        {
                            "short_label": "",
                            "min_count": 12,
                            "type": "Lab",
                            "drop_count": 2,
                            "weight": 0.25
                        },
                        {
                            "short_label": "Midterm",
                            "min_count": 1,
                            "type": "Midterm Exam",
                            "drop_count": 0,
                            "weight": 0.2
                        },
                        {
                            "short_label": "Final",
                            "min_count": 1,
                            "type": "Final Exam",
                            "drop_count": 0,
                            "weight": 0.3
                        }
                    ],
                    "GRADE_CUTOFFS": {
                        "Pass": 0.95
                    }
                },
            },
            "revisions": [
                {
                    "user_id": "test@edx.org",
                    "update": {
                        ("course", "head23456"): {
                            "display_name": "The most wonderful course",
                            "grading_policy": {
                                "GRADER": [
                                    {
                                        "min_count": 14,
                                        "weight": 0.25,
                                        "type": "Homework",
                                        "drop_count": 1,
                                        "short_label": "HWa"
                                    },
                                    {
                                        "short_label": "",
                                        "min_count": 12,
                                        "type": "Lab",
                                        "drop_count": 2,
                                        "weight": 0.25
                                    },
                                    {
                                        "short_label": "Midterm",
                                        "min_count": 1,
                                        "type": "Midterm Exam",
                                        "drop_count": 0,
                                        "weight": 0.2
                                    },
                                    {
                                        "short_label": "Final",
                                        "min_count": 1,
                                        "type": "Final Exam",
                                        "drop_count": 0,
                                        "weight": 0.3
                                    }
                                ],
                                "GRADE_CUTOFFS": {
                                    "Pass": 0.45
                                }
                            },
                        }
                    }
                }
            ]
        },
        "guestx.contender": {
            "org": "guestx",
            "course": "contender",
            "run": "run",
            "root_block_id": "head345679",
            "user_id": "test@guestx.edu",
            "fields": {
                "tabs": [
                    {
                        "type": "courseware"
                    },
                    {
                        "type": "course_info",
                        "name": "Course Info"
                    },
                    {
                        "type": "discussion",
                        "name": "Discussion"
                    },
                    {
                        "type": "wiki",
                        "name": "Wiki"
                    }
                ],
                "start": _date_field.from_json("2013-03-14T05:00"),
                "display_name": "Yet another contender",
                "grading_policy": {
                    "GRADER": [
                        {
                            "min_count": 4,
                            "weight": 0.25,
                            "type": "Homework",
                            "drop_count": 0,
                            "short_label": "HW"
                        },
                        {
                            "short_label": "Midterm",
                            "min_count": 1,
                            "type": "Midterm Exam",
                            "drop_count": 0,
                            "weight": 0.4
                        },
                        {
                            "short_label": "Final",
                            "min_count": 1,
                            "type": "Final Exam",
                            "drop_count": 0,
                            "weight": 0.35
                        }
                    ],
                    "GRADE_CUTOFFS": {
                        "Pass": 0.25
                    }
                },
            }
        },
    }

    @staticmethod
    def bootstrapDB(split_store):  # pylint: disable=invalid-name
        '''
        Sets up the initial data into the db
        '''
        for _course_id, course_spec in SplitModuleTest.COURSE_CONTENT.iteritems():
            course = split_store.create_course(
                course_spec['org'],
                course_spec['course'],
                course_spec['run'],
                course_spec['user_id'],
                master_branch=BRANCH_NAME_DRAFT,
                fields=course_spec['fields'],
                root_block_id=course_spec['root_block_id']
            )
            for revision in course_spec.get('revisions', []):
                for (block_type, block_id), fields in revision.get('update', {}).iteritems():
                    # cheat since course is most frequent
                    if course.location.block_id == block_id:
                        block = course
                    else:
                        # not easy to figure out the category but get_item won't care
                        block_usage = BlockUsageLocator.make_relative(course.location, block_type, block_id)
                        block = split_store.get_item(block_usage)
                    for key, value in fields.iteritems():
                        setattr(block, key, value)
                # create new blocks into dag: parent must already exist; thus, order is important
                new_ele_dict = {}
                for spec in revision.get('create', []):
                    if spec['parent'] in new_ele_dict:
                        parent = new_ele_dict.get(spec['parent'])
                    elif spec['parent'] == course.location.block_id:
                        parent = course
                    else:
                        block_usage = BlockUsageLocator.make_relative(course.location, spec['parent_type'], spec['parent'])
                        parent = split_store.get_item(block_usage)
                    block_id = LocalId(spec['id'])
                    child = split_store.create_xblock(
                        course.runtime, course.id, spec['category'], block_id, spec['fields'], parent_xblock=parent
                    )
                    new_ele_dict[spec['id']] = child
                course = split_store.persist_xblock_dag(course, revision['user_id'])
        # publish "testx.wonderful"
        source_course = CourseLocator(org="testx", course="wonderful", run="run", branch=BRANCH_NAME_DRAFT)
        to_publish = BlockUsageLocator(
            source_course,
            block_type='course',
            block_id="head23456"
        )
        destination = CourseLocator(org="testx", course="wonderful", run="run", branch=BRANCH_NAME_PUBLISHED)
        split_store.copy("test@edx.org", source_course, destination, [to_publish], None)

    def setUp(self):
        super(SplitModuleTest, self).setUp()
        self.user_id = random.getrandbits(32)

    def tearDown(self):
        """
        Clear persistence between each test.
        """
        collection_prefix = SplitModuleTest.MODULESTORE['DOC_STORE_CONFIG']['collection'] + '.'
        if SplitModuleTest.modulestore:
            for collection in ('active_versions', 'structures', 'definitions'):
                modulestore().db.drop_collection(collection_prefix + collection)
            # drop the modulestore to force re init
            SplitModuleTest.modulestore = None
        super(SplitModuleTest, self).tearDown()

    def findByIdInResult(self, collection, _id):  # pylint: disable=invalid-name
        """
        Result is a collection of descriptors. Find the one whose block id
        matches the _id.
        """
        for element in collection:
            if element.location.block_id == _id:
                return element


class TestHasChildrenAtDepth(SplitModuleTest):
    """Test the has_children_at_depth method of XModuleMixin. """

    @patch('xmodule.tabs.CourseTab.from_json', side_effect=mock_tab_from_json)
    def test_has_children_at_depth(self, _from_json):
        course_locator = CourseLocator(
            org='testx', course='GreekHero', run="run", branch=BRANCH_NAME_DRAFT
        )
        block_locator = BlockUsageLocator(
            course_locator, 'course', 'head12345'
        )
        block = modulestore().get_item(block_locator)

        self.assertRaises(
            ValueError, block.has_children_at_depth, -1,
        )
        self.assertTrue(block.has_children_at_depth(0))
        self.assertTrue(block.has_children_at_depth(1))
        self.assertFalse(block.has_children_at_depth(2))

        ch1 = modulestore().get_item(
            BlockUsageLocator(course_locator, 'chapter', block_id='chapter1')
        )
        self.assertFalse(ch1.has_children_at_depth(0))

        ch2 = modulestore().get_item(
            BlockUsageLocator(course_locator, 'chapter', block_id='chapter2')
        )
        self.assertFalse(ch2.has_children_at_depth(0))

        ch3 = modulestore().get_item(
            BlockUsageLocator(course_locator, 'chapter', block_id='chapter3')
        )
        self.assertTrue(ch3.has_children_at_depth(0))
        self.assertFalse(ch3.has_children_at_depth(1))


@ddt.ddt
class SplitModuleCourseTests(SplitModuleTest):
    '''
    Course CRUD operation tests
    '''

    @patch('xmodule.tabs.CourseTab.from_json', side_effect=mock_tab_from_json)
    def test_get_courses(self, _from_json):
        courses = modulestore().get_courses(branch=BRANCH_NAME_DRAFT)
        # should have gotten 3 draft courses
        self.assertEqual(len(courses), 3, "Wrong number of courses")
        # check metadata -- NOTE no promised order
        course = self.findByIdInResult(courses, "head12345")
        self.assertEqual(course.location.org, "testx")
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
        self.assertEqual(len(course.children), 3, "children")
        # check dates and graders--forces loading of descriptor
        self.assertEqual(course.edited_by, "testassist@edx.org")
        self.assertDictEqual(course.grade_cutoffs, {"Pass": 0.45})

    @patch('xmodule.tabs.CourseTab.from_json', side_effect=mock_tab_from_json)
    def test_get_courses_with_same_course_index(self, _from_json):
        """
        Test that if two courses pointing to same course index,
        get_courses should return both.
        """
        courses = modulestore().get_courses(branch=BRANCH_NAME_DRAFT)
        # Should have gotten 3 draft courses.
        self.assertEqual(len(courses), 3)

        course_index = modulestore().get_course_index_info(courses[0].id)
        # Creating a new course with same course index of another course.
        new_draft_course = modulestore().create_course(
            'testX', 'rerun_2.0', 'run_q2', 1, BRANCH_NAME_DRAFT, versions_dict=course_index['versions']
        )
        courses = modulestore().get_courses(branch=BRANCH_NAME_DRAFT)
        # Should have gotten 4 draft courses.
        self.assertEqual(len(courses), 4)
        self.assertIn(new_draft_course.id.version_agnostic(), [c.id for c in courses])

    @patch('xmodule.tabs.CourseTab.from_json', side_effect=mock_tab_from_json)
    def test_get_org_courses(self, _from_json):
        courses = modulestore().get_courses(branch=BRANCH_NAME_DRAFT, org='guestx')

        # should have gotten 1 draft courses
        self.assertEqual(len(courses), 1)

        courses = modulestore().get_courses(branch=BRANCH_NAME_DRAFT, org='testx')

        # should have gotten 2 draft courses
        self.assertEqual(len(courses), 2)

        # although this is already covered in other tests, let's
        # also not pass in org= parameter to make sure we get back
        # 3 courses
        courses = modulestore().get_courses(branch=BRANCH_NAME_DRAFT)
        self.assertEqual(len(courses), 3)

    @patch('xmodule.tabs.CourseTab.from_json', side_effect=mock_tab_from_json)
    def test_branch_requests(self, _from_json):
        # query w/ branch qualifier (both draft and published)
        def _verify_published_course(courses_published):
            """ Helper function for verifying published course. """
            self.assertEqual(len(courses_published), 1, len(courses_published))
            course = self.findByIdInResult(courses_published, "head23456")
            self.assertIsNotNone(course, "published courses")
            self.assertEqual(course.location.course_key.org, "testx")
            self.assertEqual(course.location.course_key.course, "wonderful")
            self.assertEqual(course.category, 'course', 'wrong category')
            self.assertEqual(len(course.tabs), 4, "wrong number of tabs")
            self.assertEqual(course.display_name, "The most wonderful course",
                             course.display_name)
            self.assertIsNone(course.advertised_start)
            self.assertEqual(len(course.children), 0,
                             "children")

        _verify_published_course(modulestore().get_courses(branch=BRANCH_NAME_PUBLISHED))

    def test_has_course(self):
        '''
        Test the various calling forms for has_course
        '''

        check_has_course_method(
            modulestore(),
            CourseLocator(org='testx', course='wonderful', run="run", branch=BRANCH_NAME_DRAFT),
            locator_key_fields=['org', 'course', 'run']
        )

    @patch('xmodule.tabs.CourseTab.from_json', side_effect=mock_tab_from_json)
    def test_get_course(self, _from_json):
        '''
        Test the various calling forms for get_course
        '''
        locator = CourseLocator(org='testx', course='GreekHero', run="run", branch=BRANCH_NAME_DRAFT)
        head_course = modulestore().get_course(locator)
        self.assertNotEqual(head_course.location.version_guid, head_course.previous_version)
        locator = CourseLocator(version_guid=head_course.previous_version)
        course = modulestore().get_course(locator)
        self.assertIsNone(course.location.course_key.org)
        self.assertEqual(course.location.version_guid, head_course.previous_version)
        self.assertEqual(course.category, 'course')
        self.assertEqual(len(course.tabs), 6)
        self.assertEqual(course.display_name, "The Ancient Greek Hero")
        self.assertEqual(course.graceperiod, datetime.timedelta(hours=2))
        self.assertIsNone(course.advertised_start)
        self.assertEqual(len(course.children), 0)
        self.assertNotEqual(course.definition_locator.definition_id, head_course.definition_locator.definition_id)
        # check dates and graders--forces loading of descriptor
        self.assertEqual(course.edited_by, "testassist@edx.org")
        self.assertDictEqual(course.grade_cutoffs, {"Pass": 0.55})

        locator = CourseLocator(org='testx', course='GreekHero', run="run", branch=BRANCH_NAME_DRAFT)
        course = modulestore().get_course(locator)
        self.assertEqual(course.location.course_key.org, "testx")
        self.assertEqual(course.location.course_key.course, "GreekHero")
        self.assertEqual(course.location.course_key.run, "run")
        self.assertEqual(course.category, 'course')
        self.assertEqual(len(course.tabs), 6)
        self.assertEqual(course.display_name, "The Ancient Greek Hero")
        self.assertEqual(course.advertised_start, "Fall 2013")
        self.assertEqual(len(course.children), 3)
        # check dates and graders--forces loading of descriptor
        self.assertEqual(course.edited_by, "testassist@edx.org")
        self.assertDictEqual(course.grade_cutoffs, {"Pass": 0.45})

        locator = CourseLocator(org='testx', course='wonderful', run="run", branch=BRANCH_NAME_PUBLISHED)
        course = modulestore().get_course(locator)
        published_version = course.location.version_guid

        locator = CourseLocator(org='testx', course='wonderful', run="run", branch=BRANCH_NAME_DRAFT)
        course = modulestore().get_course(locator)
        self.assertNotEqual(course.location.version_guid, published_version)

    def test_get_course_negative(self):
        # Now negative testing
        with self.assertRaises(InsufficientSpecificationError):
            modulestore().get_course(CourseLocator(org='edu', course='meh', run='blah'))
        with self.assertRaises(ItemNotFoundError):
            modulestore().get_course(CourseLocator(org='edu', course='nosuchthing', run="run", branch=BRANCH_NAME_DRAFT))
        with self.assertRaises(ItemNotFoundError):
            modulestore().get_course(CourseLocator(org='testx', course='GreekHero', run="run", branch=BRANCH_NAME_PUBLISHED))

    @patch('xmodule.tabs.CourseTab.from_json', side_effect=mock_tab_from_json)
    def test_cache(self, _from_json):
        """
        Test that the mechanics of caching work.
        """
        locator = CourseLocator(org='testx', course='GreekHero', run="run", branch=BRANCH_NAME_DRAFT)
        course = modulestore().get_course(locator)
        block_map = modulestore().cache_items(
            course.system, [BlockKey.from_usage_key(child) for child in course.children], course.id, depth=3
        )
        self.assertIn(BlockKey('chapter', 'chapter1'), block_map)
        self.assertIn(BlockKey('problem', 'problem3_2'), block_map)

    @patch('xmodule.tabs.CourseTab.from_json', side_effect=mock_tab_from_json)
    def test_course_successors(self, _from_json):
        """
        get_course_successors(course_locator, version_history_depth=1)
        """
        locator = CourseLocator(org='testx', course='GreekHero', run="run", branch=BRANCH_NAME_DRAFT)
        course = modulestore().get_course(locator)
        versions = [course.location.version_guid, course.previous_version]
        locator = CourseLocator(version_guid=course.previous_version)
        course = modulestore().get_course(locator)
        versions.append(course.previous_version)

        locator = CourseLocator(version_guid=course.previous_version)
        result = modulestore().get_course_successors(locator)
        self.assertIsInstance(result, VersionTree)
        self.assertIsNone(result.locator.org)
        self.assertEqual(result.locator.version_guid, versions[-1])
        self.assertEqual(len(result.children), 1)
        self.assertEqual(result.children[0].locator.version_guid, versions[-2])
        self.assertEqual(len(result.children[0].children), 0, "descended more than one level")

        result = modulestore().get_course_successors(locator, version_history_depth=2)
        self.assertEqual(len(result.children), 1)
        self.assertEqual(result.children[0].locator.version_guid, versions[-2])
        self.assertEqual(len(result.children[0].children), 1)

        result = modulestore().get_course_successors(locator, version_history_depth=99)
        self.assertEqual(len(result.children), 1)
        self.assertEqual(result.children[0].locator.version_guid, versions[-2])
        self.assertEqual(len(result.children[0].children), 1)
        self.assertEqual(result.children[0].children[0].locator.version_guid, versions[0])

    @patch('xmodule.tabs.CourseTab.from_json', side_effect=mock_tab_from_json)
    def test_persist_dag(self, _from_json):
        """
        try saving temporary xblocks
        """
        test_course = modulestore().create_course(
            course='course', run='2014', org='testx',
            display_name='fun test course', user_id='testbot',
            master_branch=ModuleStoreEnum.BranchName.draft
        )
        test_chapter = modulestore().create_xblock(
            test_course.system, test_course.id, 'chapter', fields={'display_name': 'chapter n'},
            parent_xblock=test_course
        )
        self.assertEqual(test_chapter.display_name, 'chapter n')
        test_def_content = '<problem>boo</problem>'
        # create child
        new_block = modulestore().create_xblock(
            test_course.system, test_course.id,
            'problem',
            fields={
                'data': test_def_content,
                'display_name': 'problem'
            },
            parent_xblock=test_chapter
        )
        self.assertIsNotNone(new_block.definition_locator)
        self.assertTrue(isinstance(new_block.definition_locator.definition_id, LocalId))
        # better to pass in persisted parent over the subdag so
        # subdag gets the parent pointer (otherwise 2 ops, persist dag, update parent children,
        # persist parent
        persisted_course = modulestore().persist_xblock_dag(test_course, 'testbot')
        self.assertEqual(len(persisted_course.children), 1)
        persisted_chapter = persisted_course.get_children()[0]
        self.assertEqual(persisted_chapter.category, 'chapter')
        self.assertEqual(persisted_chapter.display_name, 'chapter n')
        self.assertEqual(len(persisted_chapter.children), 1)
        persisted_problem = persisted_chapter.get_children()[0]
        self.assertEqual(persisted_problem.category, 'problem')
        self.assertEqual(persisted_problem.data, test_def_content)
        # update it
        persisted_problem.display_name = 'altered problem'
        persisted_problem = modulestore().update_item(persisted_problem, 'testbot')
        self.assertEqual(persisted_problem.display_name, 'altered problem')

    @patch('xmodule.tabs.CourseTab.from_json', side_effect=mock_tab_from_json)
    def test_block_generations(self, _from_json):
        """
        Test get_block_generations
        """
        test_course = modulestore().create_course(
            org='edu.harvard',
            course='history',
            run='hist101',
            display_name='history test course',
            user_id='testbot',
            master_branch=ModuleStoreEnum.BranchName.draft
        )
        chapter = modulestore().create_child(
            None, test_course.location,
            block_type='chapter',
            block_id='chapter1',
            fields={'display_name': 'chapter 1'}
        )
        sub = modulestore().create_child(
            None, chapter.location,
            block_type='vertical',
            block_id='subsection1',
            fields={'display_name': 'subsection 1'}
        )
        first_problem = modulestore().create_child(
            None, sub.location,
            block_type='problem',
            block_id='problem1',
            fields={'display_name': 'problem 1', 'data': '<problem></problem>'}
        )
        first_problem.max_attempts = 3
        first_problem.save()  # decache the above into the kvs
        updated_problem = modulestore().update_item(first_problem, 'testbot')
        self.assertIsNotNone(updated_problem.previous_version)
        self.assertEqual(updated_problem.previous_version, first_problem.update_version)
        self.assertNotEqual(updated_problem.update_version, first_problem.update_version)
        modulestore().delete_item(updated_problem.location, 'testbot')

        second_problem = modulestore().create_child(
            None, sub.location.version_agnostic(),
            block_type='problem',
            block_id='problem2',
            fields={'display_name': 'problem 2', 'data': '<problem></problem>'}
        )

        # The draft course root has 2 revisions: the published revision, and then the subsequent
        # changes to the draft revision
        version_history = modulestore().get_block_generations(test_course.location)
        self.assertIsNotNone(version_history)
        self.assertEqual(version_history.locator.version_guid, test_course.location.version_guid)
        self.assertEqual(len(version_history.children), 1)
        self.assertEqual(version_history.children[0].children, [])
        self.assertEqual(version_history.children[0].locator.version_guid, chapter.location.version_guid)

        # sub changed on add, add problem, delete problem, add problem in strict linear seq
        version_history = modulestore().get_block_generations(sub.location)
        self.assertEqual(len(version_history.children), 1)
        self.assertEqual(len(version_history.children[0].children), 1)
        self.assertEqual(len(version_history.children[0].children[0].children), 1)
        self.assertEqual(len(version_history.children[0].children[0].children[0].children), 0)

        # first and second problem may show as same usage_id; so, need to ensure their histories are right
        version_history = modulestore().get_block_generations(updated_problem.location)
        self.assertEqual(version_history.locator.version_guid, first_problem.location.version_guid)
        self.assertEqual(len(version_history.children), 1)  # updated max_attempts
        self.assertEqual(len(version_history.children[0].children), 0)

        version_history = modulestore().get_block_generations(second_problem.location)
        self.assertNotEqual(version_history.locator.version_guid, first_problem.location.version_guid)

    @ddt.data(
        ("course-v1:edx+test_course+test_run", BlockUsageLocator),
        ("ccx-v1:edX+test_course+test_run+ccx@1", CCXBlockUsageLocator),
    )
    @ddt.unpack
    def test_make_course_usage_key(self, course_id, root_block_cls):
        """Test that we get back the appropriate usage key for the root of a course key.

        In particular, we want to make sure that it properly handles CCX courses.
        """
        course_key = CourseKey.from_string(course_id)
        root_block_key = modulestore().make_course_usage_key(course_key)
        self.assertIsInstance(root_block_key, root_block_cls)
        self.assertEqual(root_block_key.block_type, "course")
        self.assertEqual(root_block_key.name, "course")


class TestCourseStructureCache(SplitModuleTest):
    """Tests for the CourseStructureCache"""

    def setUp(self):
        # use the default cache, since the `course_structure_cache`
        # is a dummy cache during testing
        self.cache = caches['default']

        # make sure we clear the cache before every test...
        self.cache.clear()
        # ... and after
        self.addCleanup(self.cache.clear)

        # make a new course:
        self.user = random.getrandbits(32)
        self.new_course = modulestore().create_course(
            'org', 'course', 'test_run', self.user, BRANCH_NAME_DRAFT,
        )

        super(TestCourseStructureCache, self).setUp()

    @patch('xmodule.modulestore.split_mongo.mongo_connection.get_cache')
    def test_course_structure_cache(self, mock_get_cache):
        # force get_cache to return the default cache so we can test
        # its caching behavior
        mock_get_cache.return_value = self.cache

        with check_mongo_calls(1):
            not_cached_structure = self._get_structure(self.new_course)

        # when cache is warmed, we should have one fewer mongo call
        with check_mongo_calls(0):
            cached_structure = self._get_structure(self.new_course)

        # now make sure that you get the same structure
        self.assertEqual(cached_structure, not_cached_structure)

    @patch('xmodule.modulestore.split_mongo.mongo_connection.get_cache')
    def test_course_structure_cache_no_cache_configured(self, mock_get_cache):
        mock_get_cache.side_effect = InvalidCacheBackendError

        with check_mongo_calls(1):
            not_cached_structure = self._get_structure(self.new_course)

        # if the cache isn't configured, we expect to have to make
        # another mongo call here if we want the same course structure
        with check_mongo_calls(1):
            cached_structure = self._get_structure(self.new_course)

        # now make sure that you get the same structure
        self.assertEqual(cached_structure, not_cached_structure)

    def test_dummy_cache(self):
        with check_mongo_calls(1):
            not_cached_structure = self._get_structure(self.new_course)

        # Since the test is using the dummy cache, it's not actually caching
        # anything
        with check_mongo_calls(1):
            cached_structure = self._get_structure(self.new_course)

        # now make sure that you get the same structure
        self.assertEqual(cached_structure, not_cached_structure)

    def _get_structure(self, course):
        """
        Helper function to get a structure from a course.
        """
        return modulestore().db_connection.get_structure(
            course.location.as_object_id(course.location.version_guid)
        )


class SplitModuleItemTests(SplitModuleTest):
    '''
    Item read tests including inheritance
    '''

    @patch('xmodule.tabs.CourseTab.from_json', side_effect=mock_tab_from_json)
    def test_has_item(self, _from_json):
        '''
        has_item(BlockUsageLocator)
        '''
        org = 'testx'
        course = 'GreekHero'
        run = 'run'
        course_locator = CourseLocator(org=org, course=course, run=run, branch=BRANCH_NAME_DRAFT)
        course = modulestore().get_course(course_locator)
        previous_version = course.previous_version
        # positive tests of various forms
        locator = course.location.map_into_course(CourseLocator(version_guid=previous_version))
        self.assertTrue(
            modulestore().has_item(locator), "couldn't find in %s" % previous_version
        )

        locator = course.location.version_agnostic()
        self.assertTrue(
            modulestore().has_item(locator),
        )
        self.assertFalse(
            modulestore().has_item(
                BlockUsageLocator(
                    locator.course_key.for_branch(BRANCH_NAME_PUBLISHED),
                    block_type=locator.block_type,
                    block_id=locator.block_id
                )
            ),
            "found in published head"
        )

        # not a course obj
        locator = BlockUsageLocator(course_locator, block_type='chapter', block_id='chapter1')
        self.assertTrue(
            modulestore().has_item(locator),
            "couldn't find chapter1"
        )

        # in published course
        locator = BlockUsageLocator(
            CourseLocator(org="testx", course="wonderful", run="run", branch=BRANCH_NAME_DRAFT),
            block_type="course",
            block_id="head23456"
        )
        self.assertTrue(
            modulestore().has_item(locator.for_branch(BRANCH_NAME_PUBLISHED))
        )

    def test_negative_has_item(self):
        # negative tests--not found
        # no such course or block
        locator = BlockUsageLocator(
            CourseLocator(org="foo", course="doesnotexist", run="run", branch=BRANCH_NAME_DRAFT),
            block_type="course",
            block_id="head23456"
        )
        self.assertFalse(modulestore().has_item(locator))
        locator = BlockUsageLocator(
            CourseLocator(org="testx", course="wonderful", run="run", branch=BRANCH_NAME_DRAFT),
            block_type="vertical",
            block_id="doesnotexist"
        )
        self.assertFalse(modulestore().has_item(locator))

    @patch('xmodule.tabs.CourseTab.from_json', side_effect=mock_tab_from_json)
    def test_get_item(self, _from_json):
        '''
        get_item(blocklocator)
        '''
        hero_locator = CourseLocator(org="testx", course="GreekHero", run="run", branch=BRANCH_NAME_DRAFT)
        course = modulestore().get_course(hero_locator)
        previous_version = course.previous_version

        # positive tests of various forms
        locator = course.location.map_into_course(CourseLocator(version_guid=previous_version))
        block = modulestore().get_item(locator)
        self.assertIsInstance(block, CourseDescriptor)
        self.assertIsInstance(modulestore().get_item(locator), CourseDescriptor)

        def verify_greek_hero(block):
            """
            Check contents of block
            """
            self.assertEqual(block.location.org, "testx")
            self.assertEqual(block.location.course, "GreekHero")
            self.assertEqual(block.location.run, "run")
            self.assertEqual(len(block.tabs), 6, "wrong number of tabs")
            self.assertEqual(block.display_name, "The Ancient Greek Hero")
            self.assertEqual(block.advertised_start, "Fall 2013")
            self.assertEqual(len(block.children), 3)
            # check dates and graders--forces loading of descriptor
            self.assertEqual(block.edited_by, "testassist@edx.org")
            self.assertDictEqual(
                block.grade_cutoffs, {"Pass": 0.45},
            )

        verify_greek_hero(modulestore().get_item(course.location))

        # try to look up other branches
        with self.assertRaises(ItemNotFoundError):
            modulestore().get_item(course.location.for_branch(BRANCH_NAME_PUBLISHED))

    def test_get_non_root(self):
        # not a course obj
        locator = BlockUsageLocator(
            CourseLocator(org='testx', course='GreekHero', run="run", branch=BRANCH_NAME_DRAFT), 'chapter', 'chapter1'
        )
        block = modulestore().get_item(locator)
        self.assertEqual(block.location.org, "testx")
        self.assertEqual(block.location.course, "GreekHero")
        self.assertEqual(block.category, 'chapter')
        self.assertEqual(block.display_name, "Hercules")
        self.assertEqual(block.edited_by, "testassist@edx.org")

        # in published course
        locator = BlockUsageLocator(
            CourseLocator(org='testx', course='wonderful', run="run", branch=BRANCH_NAME_PUBLISHED), 'course', 'head23456'
        )
        self.assertIsInstance(
            modulestore().get_item(locator),
            CourseDescriptor
        )

        # negative tests--not found
        # no such course or block
        locator = BlockUsageLocator(
            CourseLocator(org='doesnotexist', course='doesnotexist', run="run", branch=BRANCH_NAME_DRAFT), 'course', 'head23456'
        )
        with self.assertRaises(ItemNotFoundError):
            modulestore().get_item(locator)
        locator = BlockUsageLocator(
            CourseLocator(org='testx', course='wonderful', run="run", branch=BRANCH_NAME_DRAFT), 'html', 'doesnotexist'
        )
        with self.assertRaises(ItemNotFoundError):
            modulestore().get_item(locator)

    # pylint: disable=protected-access
    def test_matching(self):
        '''
        test the block and value matches help functions
        '''
        self.assertTrue(modulestore()._value_matches('help', 'help'))
        self.assertFalse(modulestore()._value_matches('help', 'Help'))
        self.assertTrue(modulestore()._value_matches(['distract', 'help', 'notme'], 'help'))
        self.assertFalse(modulestore()._value_matches(['distract', 'Help', 'notme'], 'help'))
        self.assertFalse(modulestore()._block_matches({'field': ['distract', 'Help', 'notme']}, {'field': 'help'}))
        self.assertTrue(modulestore()._block_matches(
            {'field': ['distract', 'help', 'notme'],
                'irrelevant': 2},
            {'field': 'help'}))
        self.assertTrue(modulestore()._value_matches('I need some help', re.compile(r'help')))
        self.assertTrue(modulestore()._value_matches(['I need some help', 'today'], re.compile(r'help')))
        self.assertFalse(modulestore()._value_matches('I need some help', re.compile(r'Help')))
        self.assertTrue(modulestore()._value_matches(['I need some help', 'today'], re.compile(r'Help', re.IGNORECASE)))

        self.assertTrue(modulestore()._value_matches('gotcha', {'$in': ['a', 'bunch', 'of', 'gotcha']}))
        self.assertFalse(modulestore()._value_matches('gotcha', {'$in': ['a', 'bunch', 'of', 'gotchas']}))
        self.assertFalse(modulestore()._value_matches('gotcha', {'$nin': ['a', 'bunch', 'of', 'gotcha']}))
        self.assertTrue(modulestore()._value_matches('gotcha', {'$nin': ['a', 'bunch', 'of', 'gotchas']}))

        self.assertTrue(modulestore()._block_matches({'group_access': {'1': [1]}}, {'group_access': {'$exists': True}}))
        self.assertTrue(modulestore()._block_matches({'a': 1, 'b': 2}, {'group_access': {'$exists': False}}))
        self.assertTrue(modulestore()._block_matches(
            {'a': 1, 'group_access': {'1': [1]}},
            {'a': 1, 'group_access': {'$exists': True}}))
        self.assertFalse(modulestore()._block_matches(
            {'a': 1, 'group_access': {'1': [1]}},
            {'a': 111, 'group_access': {'$exists': True}}))
        self.assertTrue(modulestore()._block_matches({'a': 1, 'b': 2}, {'a': 1, 'group_access': {'$exists': False}}))
        self.assertFalse(modulestore()._block_matches({'a': 1, 'b': 2}, {'a': 9, 'group_access': {'$exists': False}}))

        self.assertTrue(modulestore()._block_matches({'a': 1, 'b': 2}, {'a': 1}))
        self.assertFalse(modulestore()._block_matches({'a': 1, 'b': 2}, {'a': 2}))
        self.assertFalse(modulestore()._block_matches({'a': 1, 'b': 2}, {'c': 1}))
        self.assertFalse(modulestore()._block_matches({'a': 1, 'b': 2}, {'a': 1, 'c': 1}))
        self.assertTrue(modulestore()._block_matches({'a': 1, 'b': 2}, {'a': lambda i: 0 < i < 2}))

    def test_get_items(self):
        '''
        get_items(locator, qualifiers, [branch])
        '''
        locator = CourseLocator(org='testx', course='GreekHero', run="run", branch=BRANCH_NAME_DRAFT)
        # get all modules
        matches = modulestore().get_items(locator)
        self.assertEqual(len(matches), 7)
        matches = modulestore().get_items(locator)
        self.assertEqual(len(matches), 7)
        matches = modulestore().get_items(locator, qualifiers={'category': 'chapter'})
        self.assertEqual(len(matches), 3)
        matches = modulestore().get_items(locator, qualifiers={'category': 'garbage'})
        self.assertEqual(len(matches), 0)
        matches = modulestore().get_items(locator, qualifiers={'name': 'chapter1'})
        self.assertEqual(len(matches), 1)
        matches = modulestore().get_items(locator, qualifiers={'name': ['chapter1', 'chapter2']})
        self.assertEqual(len(matches), 2)
        matches = modulestore().get_items(
            locator,
            qualifiers={'category': 'chapter'},
            settings={'display_name': re.compile(r'Hera')},
        )
        self.assertEqual(len(matches), 2)
        matches = modulestore().get_items(locator, settings={'group_access': {'$exists': True}})
        self.assertEqual(len(matches), 1)
        matches = modulestore().get_items(locator, settings={'group_access': {'$exists': False}})
        self.assertEqual(len(matches), 6)

    def test_get_parents(self):
        '''
        get_parent_location(locator): BlockUsageLocator
        '''
        locator = BlockUsageLocator(
            CourseLocator(org='testx', course='GreekHero', run="run", branch=BRANCH_NAME_DRAFT),
            'chapter', block_id='chapter1'
        )
        parent = modulestore().get_parent_location(locator)
        self.assertIsNotNone(parent)
        self.assertEqual(parent.block_id, 'head12345')
        self.assertEqual(parent.org, "testx")
        self.assertEqual(parent.course, "GreekHero")
        locator = locator.course_key.make_usage_key('chapter', 'chapter2')
        parent = modulestore().get_parent_location(locator)
        self.assertIsNotNone(parent)
        self.assertEqual(parent.block_id, 'head12345')
        locator = locator.course_key.make_usage_key('garbage', 'nosuchblock')
        parent = modulestore().get_parent_location(locator)
        self.assertIsNone(parent)

    @patch('xmodule.tabs.CourseTab.from_json', side_effect=mock_tab_from_json)
    def test_get_children(self, _from_json):
        """
        Test the existing get_children method on xdescriptors
        """
        locator = BlockUsageLocator(
            CourseLocator(org='testx', course='GreekHero', run="run", branch=BRANCH_NAME_DRAFT), 'course', 'head12345'
        )
        block = modulestore().get_item(locator)
        children = block.get_children()
        expected_ids = [
            "chapter1", "chapter2", "chapter3"
        ]
        for child in children:
            self.assertEqual(child.category, "chapter")
            self.assertIn(child.location.block_id, expected_ids)
            expected_ids.remove(child.location.block_id)
        self.assertEqual(len(expected_ids), 0)


def version_agnostic(children):
    """
    children: list of descriptors
    Returns the `children` list with each member version-agnostic
    """
    return [child.version_agnostic() for child in children]


class TestItemCrud(SplitModuleTest):
    """
    Test create update and delete of items
    """
    # DHM do I need to test this case which I believe won't work:
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
        create_item(user, location, category, definition_locator=None, fields): new_desciptor
        """
        # grab link to course to ensure new versioning works
        locator = CourseLocator(org='testx', course='GreekHero', run="run", branch=BRANCH_NAME_DRAFT)
        premod_course = modulestore().get_course(locator)
        premod_history = modulestore().get_course_history_info(locator)
        # add minimal one w/o a parent
        category = 'sequential'
        new_module = modulestore().create_item(
            'user123', locator, category,
            fields={'display_name': 'new sequential'}
        )
        # check that course version changed and course's previous is the other one
        self.assertEqual(new_module.location.course, "GreekHero")
        self.assertNotEqual(new_module.location.version_guid, premod_course.location.version_guid)
        self.assertIsNone(locator.version_guid, "Version inadvertently filled in")
        current_course = modulestore().get_course(locator)
        self.assertEqual(new_module.location.version_guid, current_course.location.version_guid)

        history_info = modulestore().get_course_history_info(current_course.location.course_key)
        self.assertEqual(history_info['previous_version'], premod_course.location.version_guid)
        self.assertEqual(history_info['original_version'], premod_history['original_version'])
        self.assertEqual(history_info['edited_by'], "user123")
        # check block's info: category, definition_locator, and display_name
        self.assertEqual(new_module.category, 'sequential')
        self.assertIsNotNone(new_module.definition_locator)
        self.assertEqual(new_module.display_name, 'new sequential')
        # check that block does not exist in previous version
        locator = new_module.location.map_into_course(
            CourseLocator(version_guid=premod_course.location.version_guid)
        )
        with self.assertRaises(ItemNotFoundError):
            modulestore().get_item(locator)

    def test_create_parented_item(self):
        """
        Test create_item w/ specifying the parent of the new item
        """
        locator = BlockUsageLocator(
            CourseLocator(org='testx', course='GreekHero', run="run", branch=BRANCH_NAME_DRAFT),
            'chapter', block_id='chapter2'
        )
        original = modulestore().get_item(locator)

        locator = BlockUsageLocator(
            CourseLocator(org='testx', course='wonderful', run="run", branch=BRANCH_NAME_DRAFT), 'course', 'head23456'
        )
        premod_course = modulestore().get_course(locator.course_key)
        category = 'chapter'
        new_module = modulestore().create_child(
            'user123', locator, category,
            fields={'display_name': 'new chapter'},
            definition_locator=original.definition_locator
        )
        # check that course version changed and course's previous is the other one
        self.assertNotEqual(new_module.location.version_guid, premod_course.location.version_guid)
        parent = modulestore().get_item(locator)
        self.assertIn(new_module.location.version_agnostic(), version_agnostic(parent.children))
        self.assertEqual(new_module.definition_locator.definition_id, original.definition_locator.definition_id)

    def test_unique_naming(self):
        """
        Check that 2 modules of same type get unique block_ids. Also check that if creation provides
        a definition id and new def data that it branches the definition in the db.
        Actually, this tries to test all create_item features not tested above.
        """
        locator = BlockUsageLocator(
            CourseLocator(org='testx', course='GreekHero', run="run", branch=BRANCH_NAME_DRAFT),
            'problem', block_id='problem1'
        )
        original = modulestore().get_item(locator)

        locator = BlockUsageLocator(
            CourseLocator(org='guestx', course='contender', run="run", branch=BRANCH_NAME_DRAFT), 'course', 'head345679'
        )
        category = 'problem'
        new_payload = "<problem>empty</problem>"
        new_module = modulestore().create_child(
            'anotheruser', locator, category,
            fields={'display_name': 'problem 1', 'data': new_payload},
        )
        another_payload = "<problem>not empty</problem>"
        another_module = modulestore().create_child(
            'anotheruser', locator, category,
            fields={'display_name': 'problem 2', 'data': another_payload},
            definition_locator=original.definition_locator,
        )
        # check that course version changed and course's previous is the other one
        parent = modulestore().get_item(locator)
        self.assertNotEqual(new_module.location.block_id, another_module.location.block_id)
        self.assertIn(new_module.location.version_agnostic(), version_agnostic(parent.children))
        self.assertIn(another_module.location.version_agnostic(), version_agnostic(parent.children))
        self.assertEqual(new_module.data, new_payload)
        self.assertEqual(another_module.data, another_payload)
        # check definition histories
        new_history = modulestore().get_definition_history_info(new_module.definition_locator)
        self.assertIsNone(new_history['previous_version'])
        self.assertEqual(new_history['original_version'], new_module.definition_locator.definition_id)
        self.assertEqual(new_history['edited_by'], "anotheruser")
        another_history = modulestore().get_definition_history_info(another_module.definition_locator)
        self.assertEqual(another_history['previous_version'], original.definition_locator.definition_id)

    def test_encoded_naming(self):
        """
        Check that using odd characters in block id don't break ability to add and retrieve block.
        """
        course_key = CourseLocator(org='guestx', course='contender', run="run", branch=BRANCH_NAME_DRAFT)
        parent_locator = BlockUsageLocator(course_key, 'course', block_id="head345679")
        chapter_locator = BlockUsageLocator(course_key, 'chapter', block_id="foo.bar_-~:0")
        modulestore().create_child(
            'anotheruser', parent_locator, 'chapter',
            block_id=chapter_locator.block_id,
            fields={'display_name': 'chapter 99'},
        )
        # check that course version changed and course's previous is the other one
        new_module = modulestore().get_item(chapter_locator)
        self.assertEqual(new_module.location.block_id, "foo.bar_-~:0")  # hardcode to ensure BUL init didn't change
        # now try making that a parent of something
        new_payload = "<problem>empty</problem>"
        problem_locator = BlockUsageLocator(course_key, 'problem', block_id="prob.bar_-~:99a")
        modulestore().create_child(
            'anotheruser', chapter_locator, 'problem',
            block_id=problem_locator.block_id,
            fields={'display_name': 'chapter 99', 'data': new_payload},
        )
        # check that course version changed and course's previous is the other one
        new_module = modulestore().get_item(problem_locator)
        self.assertEqual(new_module.location.block_id, problem_locator.block_id)
        chapter = modulestore().get_item(chapter_locator)
        self.assertIn(problem_locator, version_agnostic(chapter.children))

    def test_create_bulk_operations(self):
        """
        Test create_item using bulk_operations
        """
        # start transaction w/ simple creation
        user = random.getrandbits(32)
        course_key = CourseLocator('test_org', 'test_transaction', 'test_run')
        with modulestore().bulk_operations(course_key):
            new_course = modulestore().create_course('test_org', 'test_transaction', 'test_run', user, BRANCH_NAME_DRAFT)
            new_course_locator = new_course.id
            index_history_info = modulestore().get_course_history_info(new_course.location.course_key)
            course_block_prev_version = new_course.previous_version
            course_block_update_version = new_course.update_version
            self.assertIsNotNone(new_course_locator.version_guid, "Want to test a definite version")
            versionless_course_locator = new_course_locator.version_agnostic()

            # positive simple case: no force, add chapter
            new_ele = modulestore().create_child(
                user, new_course.location, 'chapter',
                fields={'display_name': 'chapter 1'},
            )
            # version info shouldn't change
            self.assertEqual(new_ele.update_version, course_block_update_version)
            self.assertEqual(new_ele.update_version, new_ele.location.version_guid)
            refetch_course = modulestore().get_course(versionless_course_locator)
            self.assertEqual(refetch_course.location.version_guid, new_course.location.version_guid)
            self.assertEqual(refetch_course.previous_version, course_block_prev_version)
            self.assertEqual(refetch_course.update_version, course_block_update_version)
            refetch_index_history_info = modulestore().get_course_history_info(refetch_course.location.course_key)
            self.assertEqual(refetch_index_history_info, index_history_info)
            self.assertIn(new_ele.location.version_agnostic(), version_agnostic(refetch_course.children))

            # try to create existing item
            with self.assertRaises(DuplicateItemError):
                _fail = modulestore().create_child(
                    user, new_course.location, 'chapter',
                    block_id=new_ele.location.block_id,
                    fields={'display_name': 'chapter 2'},
                )

        # start a new transaction
        with modulestore().bulk_operations(course_key):
            new_ele = modulestore().create_child(
                user, new_course.location, 'chapter',
                fields={'display_name': 'chapter 2'},
            )
            transaction_guid = new_ele.location.version_guid
            # ensure force w/ continue gives exception
            with self.assertRaises(VersionConflictError):
                _fail = modulestore().create_child(
                    user, new_course.location, 'chapter',
                    fields={'display_name': 'chapter 2'},
                    force=True
                )

            # ensure trying to continue the old one gives exception
            with self.assertRaises(VersionConflictError):
                _fail = modulestore().create_child(
                    user, new_course.location, 'chapter',
                    fields={'display_name': 'chapter 3'},
                )

            # add new child to old parent in continued (leave off version_guid)
            course_module_locator = new_course.location.version_agnostic()
            new_ele = modulestore().create_child(
                user, course_module_locator, 'chapter',
                fields={'display_name': 'chapter 4'},
            )
            self.assertNotEqual(new_ele.update_version, course_block_update_version)
            self.assertEqual(new_ele.location.version_guid, transaction_guid)

            # check children, previous_version
            refetch_course = modulestore().get_course(versionless_course_locator)
            self.assertIn(new_ele.location.version_agnostic(), version_agnostic(refetch_course.children))
            self.assertEqual(refetch_course.previous_version, course_block_update_version)
            self.assertEqual(refetch_course.update_version, transaction_guid)

    def test_bulk_ops_org_filtering(self):
        """
        Make sure of proper filtering when using bulk operations and
        calling get_courses with an 'org' filter
        """

        # start transaction w/ simple creation
        user = random.getrandbits(32)
        course_key = CourseLocator('test_org', 'test_transaction', 'test_run')
        with modulestore().bulk_operations(course_key):
            modulestore().create_course('test_org', 'test_transaction', 'test_run', user, BRANCH_NAME_DRAFT)

            courses = modulestore().get_courses(branch=BRANCH_NAME_DRAFT, org='test_org')
            self.assertEqual(len(courses), 1)
            self.assertEqual(courses[0].id.org, course_key.org)
            self.assertEqual(courses[0].id.course, course_key.course)
            self.assertEqual(courses[0].id.run, course_key.run)

            courses = modulestore().get_courses(branch=BRANCH_NAME_DRAFT, org='other_org')
            self.assertEqual(len(courses), 0)

        # re-assert after the end of the with scope
        courses = modulestore().get_courses(branch=BRANCH_NAME_DRAFT, org='test_org')
        self.assertEqual(len(courses), 1)
        self.assertEqual(courses[0].id.org, course_key.org)
        self.assertEqual(courses[0].id.course, course_key.course)
        self.assertEqual(courses[0].id.run, course_key.run)

        courses = modulestore().get_courses(branch=BRANCH_NAME_DRAFT, org='other_org')
        self.assertEqual(len(courses), 0)

    def test_update_metadata(self):
        """
        test updating an items metadata ensuring the definition doesn't version but the course does if it should
        """
        locator = BlockUsageLocator(
            CourseLocator(org="testx", course="GreekHero", run="run", branch=BRANCH_NAME_DRAFT),
            'problem', block_id="problem3_2"
        )
        problem = modulestore().get_item(locator)
        pre_def_id = problem.definition_locator.definition_id
        pre_version_guid = problem.location.version_guid
        self.assertIsNotNone(pre_def_id)
        self.assertIsNotNone(pre_version_guid)
        self.assertNotEqual(problem.max_attempts, 4, "Invalidates rest of test")

        problem.max_attempts = 4
        problem.save()  # decache above setting into the kvs
        updated_problem = modulestore().update_item(problem, self.user_id)
        # check that course version changed and course's previous is the other one
        self.assertEqual(updated_problem.definition_locator.definition_id, pre_def_id)
        self.assertNotEqual(updated_problem.location.version_guid, pre_version_guid)
        self.assertEqual(updated_problem.max_attempts, 4)
        # refetch to ensure original didn't change
        original_location = problem.location.map_into_course(CourseLocator(version_guid=pre_version_guid))
        problem = modulestore().get_item(original_location)
        self.assertNotEqual(problem.max_attempts, 4, "original changed")

        current_course = modulestore().get_course(locator.course_key)
        self.assertEqual(updated_problem.location.version_guid, current_course.location.version_guid)

        history_info = modulestore().get_course_history_info(current_course.location.course_key)
        self.assertEqual(history_info['previous_version'], pre_version_guid)
        self.assertEqual(history_info['edited_by'], self.user_id)

    def test_update_children(self):
        """
        test updating an item's children ensuring the definition doesn't version but the course does if it should
        """
        locator = BlockUsageLocator(
            CourseLocator(org='testx', course='GreekHero', run="run", branch=BRANCH_NAME_DRAFT), 'chapter', 'chapter3'
        )
        block = modulestore().get_item(locator)
        pre_def_id = block.definition_locator.definition_id
        pre_version_guid = block.location.version_guid

        # reorder children
        self.assertGreater(len(block.children), 0, "meaningless test")
        moved_child = block.children.pop()
        block.save()  # decache model changes
        updated_problem = modulestore().update_item(block, self.user_id)
        # check that course version changed and course's previous is the other one
        self.assertEqual(updated_problem.definition_locator.definition_id, pre_def_id)
        self.assertNotEqual(updated_problem.location.version_guid, pre_version_guid)
        self.assertEqual(version_agnostic(updated_problem.children), version_agnostic(block.children))
        self.assertNotIn(moved_child, version_agnostic(updated_problem.children))
        locator = locator.course_key.make_usage_key('chapter', "chapter1")
        other_block = modulestore().get_item(locator)
        other_block.children.append(moved_child)
        other_updated = modulestore().update_item(other_block, self.user_id)
        self.assertIn(moved_child.version_agnostic(), version_agnostic(other_updated.children))

    @patch('xmodule.tabs.CourseTab.from_json', side_effect=mock_tab_from_json)
    def test_update_definition(self, _from_json):
        """
        test updating an item's definition: ensure it gets versioned as well as the course getting versioned
        """
        locator = BlockUsageLocator(
            CourseLocator(org='testx', course='GreekHero', run="run", branch=BRANCH_NAME_DRAFT), 'course', 'head12345'
        )
        block = modulestore().get_item(locator)
        pre_def_id = block.definition_locator.definition_id
        pre_version_guid = block.location.version_guid

        block.grading_policy['GRADER'][0]['min_count'] = 13
        block.save()  # decache model changes
        updated_block = modulestore().update_item(block, self.user_id)

        self.assertNotEqual(updated_block.definition_locator.definition_id, pre_def_id)
        self.assertNotEqual(updated_block.location.version_guid, pre_version_guid)
        self.assertEqual(updated_block.grading_policy['GRADER'][0]['min_count'], 13)

    def test_update_manifold(self):
        """
        Test updating metadata, children, and definition in a single call ensuring all the versioning occurs
        """
        locator = BlockUsageLocator(
            CourseLocator('testx', 'GreekHero', 'run', branch=BRANCH_NAME_DRAFT),
            'problem', block_id='problem1'
        )
        original = modulestore().get_item(locator)
        # first add 2 children to the course for the update to manipulate
        locator = BlockUsageLocator(
            CourseLocator('guestx', 'contender', 'run', branch=BRANCH_NAME_DRAFT),
            'course', block_id="head345679"
        )
        category = 'problem'
        new_payload = "<problem>empty</problem>"
        modulestore().create_child(
            'test_update_manifold', locator, category,
            fields={'display_name': 'problem 1', 'data': new_payload},
        )
        another_payload = "<problem>not empty</problem>"
        modulestore().create_child(
            'test_update_manifold', locator, category,
            fields={'display_name': 'problem 2', 'data': another_payload},
            definition_locator=original.definition_locator,
        )
        # pylint: disable=protected-access
        modulestore()._clear_cache()

        # now begin the test
        block = modulestore().get_item(locator)
        pre_def_id = block.definition_locator.definition_id
        pre_version_guid = block.location.version_guid

        self.assertNotEqual(block.grading_policy['GRADER'][0]['min_count'], 13)
        block.grading_policy['GRADER'][0]['min_count'] = 13
        block.children = block.children[1:] + [block.children[0]]
        block.advertised_start = "Soon"

        block.save()  # decache model changes
        updated_block = modulestore().update_item(block, self.user_id)
        self.assertNotEqual(updated_block.definition_locator.definition_id, pre_def_id)
        self.assertNotEqual(updated_block.location.version_guid, pre_version_guid)
        self.assertEqual(updated_block.grading_policy['GRADER'][0]['min_count'], 13)
        self.assertEqual(updated_block.children[0].version_agnostic(), block.children[0].version_agnostic())
        self.assertEqual(updated_block.advertised_start, "Soon")

    def test_delete_item(self):
        course = self.create_course_for_deletion()
        with self.assertRaises(ValueError):
            modulestore().delete_item(course.location, self.user_id)
        reusable_location = course.id.version_agnostic().for_branch(BRANCH_NAME_DRAFT)

        # delete a leaf
        problems = modulestore().get_items(reusable_location, qualifiers={'category': 'problem'})
        locn_to_del = problems[0].location
        new_course_loc = modulestore().delete_item(locn_to_del, self.user_id)
        deleted = locn_to_del.version_agnostic()
        self.assertFalse(modulestore().has_item(deleted))
        with self.assertRaises(VersionConflictError):
            modulestore().has_item(locn_to_del)
        with self.assertRaises(ValueError):
            modulestore().delete_item(deleted, self.user_id)

        self.assertTrue(modulestore().has_item(locn_to_del.course_agnostic()))
        self.assertNotEqual(new_course_loc.version_guid, course.location.version_guid)

        # delete a subtree
        nodes = modulestore().get_items(reusable_location, qualifiers={'category': 'chapter'})
        new_course_loc = modulestore().delete_item(nodes[0].location, self.user_id)
        # check subtree

        def check_subtree(node):
            """
            Check contents of subtree recursively
            """
            if node:
                node_loc = node.location
                self.assertFalse(
                    modulestore().has_item(node_loc.version_agnostic())
                )
                self.assertTrue(modulestore().has_item(node_loc.course_agnostic()))
                if node.has_children:
                    for sub in node.get_children():
                        check_subtree(sub)
        check_subtree(nodes[0])

    def create_course_for_deletion(self):
        """
        Create a course we can delete
        """
        course = modulestore().create_course('nihilx', 'deletion', 'run', 'deleting_user', BRANCH_NAME_DRAFT)
        root = course.location.version_agnostic().for_branch(BRANCH_NAME_DRAFT)
        for _ in range(4):
            self.create_subtree_for_deletion(root, ['chapter', 'vertical', 'problem'])
        return modulestore().get_item(root)

    def create_subtree_for_deletion(self, parent, category_queue):
        """
        Create a subtree in the tb deleted course
        """
        if not category_queue:
            return
        node = modulestore().create_child(
            'deleting_user', parent.version_agnostic(), category_queue[0]
        )
        node_loc = node.location.map_into_course(parent.course_key)
        for _ in range(4):
            self.create_subtree_for_deletion(node_loc, category_queue[1:])

    def test_split_modulestore_create_child_with_position(self):
        """
        This test is designed to hit a specific set of use cases having to do with
        the child positioning logic found in split_mongo/split.py:create_child()
        """
        # Set up the split module store
        store = modulestore()
        user = random.getrandbits(32)
        course_key = CourseLocator('test_org', 'test_transaction', 'test_run')
        with store.bulk_operations(course_key):
            new_course = store.create_course('test_org', 'test_transaction', 'test_run', user, BRANCH_NAME_DRAFT)
            new_course_locator = new_course.id
            versionless_course_locator = new_course_locator.version_agnostic()
            first_child = store.create_child(
                self.user_id,
                new_course.location,
                "chapter"
            )
            refetch_course = store.get_course(versionless_course_locator)
            second_child = store.create_child(
                self.user_id,
                refetch_course.location,
                "chapter",
                position=0
            )

            # First child should have been moved to second position, and better child takes the lead
            refetch_course = store.get_course(versionless_course_locator)
            children = refetch_course.get_children()
            self.assertEqual(unicode(children[1].location), unicode(first_child.location))
            self.assertEqual(unicode(children[0].location), unicode(second_child.location))

            # Clean up the data so we don't break other tests which apparently expect a particular state
            store.delete_course(refetch_course.id, user)


class TestCourseCreation(SplitModuleTest):
    """
    Test create_course
    """
    def test_simple_creation(self):
        """
        The simplest case but probing all expected results from it.
        """
        # Oddly getting differences of 200nsec
        new_course = modulestore().create_course(
            'test_org', 'test_course', 'test_run', 'create_user', BRANCH_NAME_DRAFT
        )
        new_locator = new_course.location
        # check index entry
        index_info = modulestore().get_course_index_info(new_locator.course_key)
        self.assertEqual(index_info['org'], 'test_org')
        self.assertEqual(index_info['edited_by'], 'create_user')
        # check structure info
        structure_info = modulestore().get_course_history_info(new_locator.course_key)
        self.assertEqual(structure_info['original_version'], index_info['versions'][BRANCH_NAME_DRAFT])
        self.assertIsNone(structure_info['previous_version'])

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
        original_locator = CourseLocator(org='testx', course='wonderful', run="run", branch=BRANCH_NAME_DRAFT)
        original_index = modulestore().get_course_index_info(original_locator)
        new_draft = modulestore().create_course(
            'best', 'leech', 'leech_run', 'leech_master', BRANCH_NAME_DRAFT,
            versions_dict=original_index['versions'])
        new_draft_locator = new_draft.location
        self.assertRegexpMatches(new_draft_locator.org, 'best')
        # the edited_by and other meta fields on the new course will be the original author not this one
        self.assertEqual(new_draft.edited_by, 'test@edx.org')
        self.assertEqual(new_draft_locator.version_guid, original_index['versions'][BRANCH_NAME_DRAFT])
        # however the edited_by and other meta fields on course_index will be this one
        new_index = modulestore().get_course_index_info(new_draft_locator.course_key)
        self.assertEqual(new_index['edited_by'], 'leech_master')

        new_published_locator = new_draft_locator.course_key.for_branch(BRANCH_NAME_PUBLISHED)
        new_published = modulestore().get_course(new_published_locator)
        self.assertEqual(new_published.edited_by, 'test@edx.org')
        self.assertEqual(new_published.location.version_guid, original_index['versions'][BRANCH_NAME_PUBLISHED])

        # changing this course will not change the original course
        # using new_draft.location will insert the chapter under the course root
        new_item = modulestore().create_child(
            'leech_master', new_draft.location, 'chapter',
            fields={'display_name': 'new chapter'}
        )
        new_draft_locator = new_draft_locator.course_key.version_agnostic()
        new_index = modulestore().get_course_index_info(new_draft_locator)
        self.assertNotEqual(new_index['versions'][BRANCH_NAME_DRAFT], original_index['versions'][BRANCH_NAME_DRAFT])
        new_draft = modulestore().get_course(new_draft_locator)
        self.assertEqual(new_item.edited_by, 'leech_master')
        self.assertNotEqual(new_item.location.version_guid, original_index['versions'][BRANCH_NAME_DRAFT])
        self.assertNotEqual(new_draft.location.version_guid, original_index['versions'][BRANCH_NAME_DRAFT])
        structure_info = modulestore().get_course_history_info(new_draft_locator)
        self.assertEqual(structure_info['edited_by'], 'leech_master')

        original_course = modulestore().get_course(original_locator)
        self.assertEqual(original_course.location.version_guid, original_index['versions'][BRANCH_NAME_DRAFT])

    def test_derived_course(self):
        """
        Create a new course which overrides metadata and course_data
        """
        original_locator = CourseLocator(org='guestx', course='contender', run="run", branch=BRANCH_NAME_DRAFT)
        original = modulestore().get_course(original_locator)
        original_index = modulestore().get_course_index_info(original_locator)
        fields = {
            'grading_policy': original.grading_policy,
            'display_name': 'Derivative',
        }
        fields['grading_policy']['GRADE_CUTOFFS'] = {'A': .9, 'B': .8, 'C': .65}
        new_draft = modulestore().create_course(
            'counter', 'leech', 'leech_run', 'leech_master', BRANCH_NAME_DRAFT,
            versions_dict={BRANCH_NAME_DRAFT: original_index['versions'][BRANCH_NAME_DRAFT]},
            fields=fields
        )
        new_draft_locator = new_draft.location
        self.assertRegexpMatches(new_draft_locator.org, 'counter')
        # the edited_by and other meta fields on the new course will be the original author not this one
        self.assertEqual(new_draft.edited_by, 'leech_master')
        self.assertNotEqual(new_draft_locator.version_guid, original_index['versions'][BRANCH_NAME_DRAFT])
        # however the edited_by and other meta fields on course_index will be this one
        new_index = modulestore().get_course_index_info(new_draft_locator.course_key)
        self.assertEqual(new_index['edited_by'], 'leech_master')
        self.assertEqual(new_draft.display_name, fields['display_name'])
        self.assertDictEqual(
            new_draft.grading_policy['GRADE_CUTOFFS'],
            fields['grading_policy']['GRADE_CUTOFFS']
        )

    @patch('xmodule.tabs.CourseTab.from_json', side_effect=mock_tab_from_json)
    def test_update_course_index(self, _from_json):
        """
        Test the versions pointers. NOTE: you can change the org, course, or other things, but
        it's not clear how you'd find them again or associate them w/ existing student history since
        we use course_key so many places as immutable.
        """
        locator = CourseLocator(org='testx', course='GreekHero', run="run", branch=BRANCH_NAME_DRAFT)
        course_info = modulestore().get_course_index_info(locator)

        # an allowed but not necessarily recommended way to revert the draft version
        head_course = modulestore().get_course(locator)
        versions = course_info['versions']
        versions[BRANCH_NAME_DRAFT] = head_course.previous_version
        modulestore().update_course_index(None, course_info)
        course = modulestore().get_course(locator)
        self.assertEqual(course.location.version_guid, versions[BRANCH_NAME_DRAFT])

        # an allowed but not recommended way to publish a course
        versions[BRANCH_NAME_PUBLISHED] = versions[BRANCH_NAME_DRAFT]
        modulestore().update_course_index(None, course_info)
        course = modulestore().get_course(locator.for_branch(BRANCH_NAME_PUBLISHED))
        self.assertEqual(course.location.version_guid, versions[BRANCH_NAME_DRAFT])

    def test_create_with_root(self):
        """
        Test create_course with a specified root id and category
        """
        user = random.getrandbits(32)
        new_course = modulestore().create_course(
            'test_org', 'test_transaction', 'test_run', user, BRANCH_NAME_DRAFT,
            root_block_id='top', root_category='chapter'
        )
        self.assertEqual(new_course.location.block_id, 'top')
        self.assertEqual(new_course.category, 'chapter')
        # look at db to verify
        db_structure = modulestore().db_connection.get_structure(
            new_course.location.as_object_id(new_course.location.version_guid)
        )
        self.assertIsNotNone(db_structure, "Didn't find course")
        self.assertNotIn(BlockKey('course', 'course'), db_structure['blocks'])
        self.assertIn(BlockKey('chapter', 'top'), db_structure['blocks'])
        self.assertEqual(db_structure['blocks'][BlockKey('chapter', 'top')].block_type, 'chapter')

    def test_create_id_dupe(self):
        """
        Test create_course rejects duplicate id
        """
        user = random.getrandbits(32)
        courses = modulestore().get_courses(BRANCH_NAME_DRAFT)
        with self.assertRaises(DuplicateCourseError):
            dupe_course_key = courses[0].location.course_key
            modulestore().create_course(
                dupe_course_key.org, dupe_course_key.course, dupe_course_key.run, user, BRANCH_NAME_DRAFT
            )

    @patch('xmodule.tabs.CourseTab.from_json', side_effect=mock_tab_from_json)
    def test_bulk_ops_get_courses(self, _from_json):
        """
        Test get_courses when some are created, updated, and deleted w/in a bulk operation
        """
        # create 3 courses before bulk operation
        split_store = modulestore()

        user = random.getrandbits(32)
        to_be_created = split_store.make_course_key('new', 'created', 'course')
        with split_store.bulk_operations(to_be_created):
            split_store.create_course(
                to_be_created.org, to_be_created.course, to_be_created.run, user, master_branch=BRANCH_NAME_DRAFT,
            )

            modified_course_loc = CourseLocator(org='testx', course='GreekHero', run="run", branch=BRANCH_NAME_DRAFT)
            with split_store.bulk_operations(modified_course_loc):
                modified_course = modulestore().get_course(modified_course_loc)
                modified_course.advertised_start = 'coming soon to a theater near you'
                split_store.update_item(modified_course, user)

                to_be_deleted = split_store.make_course_key("guestx", "contender", "run")
                with split_store.bulk_operations(to_be_deleted):
                    split_store.delete_course(to_be_deleted, user)

                    # now get_courses
                    courses = split_store.get_courses(BRANCH_NAME_DRAFT)

                    self.assertEqual(len(courses), 3)
                    course_ids = [course.id.for_branch(None) for course in courses]
                    self.assertNotIn(to_be_deleted, course_ids)
                    self.assertIn(to_be_created, course_ids)
                    fetched_modified = [course for course in courses if course.id == modified_course_loc][0]
                    self.assertEqual(fetched_modified.advertised_start, modified_course.advertised_start)


class TestInheritance(SplitModuleTest):
    """
    Test the metadata inheritance mechanism.
    """
    @patch('xmodule.tabs.CourseTab.from_json', side_effect=mock_tab_from_json)
    def test_inheritance(self, _from_json):
        """
        The actual test
        """
        # Note, not testing value where defined (course) b/c there's no
        # defined accessor for it on CourseDescriptor.
        locator = BlockUsageLocator(
            CourseLocator(org='testx', course='GreekHero', run="run", branch=BRANCH_NAME_DRAFT), 'problem', 'problem3_2'
        )
        node = modulestore().get_item(locator)
        # inherited
        self.assertEqual(node.graceperiod, datetime.timedelta(hours=2))
        locator = BlockUsageLocator(
            CourseLocator(org='testx', course='GreekHero', run="run", branch=BRANCH_NAME_DRAFT), 'problem', 'problem1'
        )
        node = modulestore().get_item(locator)
        # overridden
        self.assertEqual(node.graceperiod, datetime.timedelta(hours=4))

    def test_inheritance_not_saved(self):
        """
        Was saving inherited settings with updated blocks causing inheritance to be sticky
        """
        # set on parent, retrieve child, verify setting
        chapter = modulestore().get_item(
            BlockUsageLocator(
                CourseLocator(org='testx', course='GreekHero', run="run", branch=BRANCH_NAME_DRAFT), 'chapter', 'chapter3'
            )
        )
        problem = modulestore().get_item(
            BlockUsageLocator(
                CourseLocator(org='testx', course='GreekHero', run="run", branch=BRANCH_NAME_DRAFT), 'problem', 'problem3_2'
            )
        )
        self.assertFalse(problem.visible_to_staff_only)

        chapter.visible_to_staff_only = True
        modulestore().update_item(chapter, self.user_id)
        problem = modulestore().get_item(problem.location.version_agnostic())
        self.assertTrue(problem.visible_to_staff_only)

        # unset on parent, retrieve child, verify unset
        chapter = modulestore().get_item(chapter.location.version_agnostic())
        del chapter.visible_to_staff_only
        modulestore().update_item(chapter, self.user_id)

        problem = modulestore().get_item(problem.location.version_agnostic())
        self.assertFalse(problem.visible_to_staff_only)

    def test_dynamic_inheritance(self):
        """
        Test inheritance for create_item with and without a parent pointer
        """
        course_key = CourseLocator(org='testx', course='GreekHero', run="run", branch=BRANCH_NAME_DRAFT)
        chapter = modulestore().get_item(BlockUsageLocator(course_key, 'chapter', 'chapter3'))

        chapter.visible_to_staff_only = True
        orphan_problem = modulestore().create_item(self.user_id, course_key, 'problem')
        self.assertFalse(orphan_problem.visible_to_staff_only)
        parented_problem = modulestore().create_child(self.user_id, chapter.location.version_agnostic(), 'problem')
        # FIXME LMS-11376
#         self.assertTrue(parented_problem.visible_to_staff_only)

        orphan_problem = modulestore().create_xblock(chapter.runtime, course_key, 'problem')
        self.assertFalse(orphan_problem.visible_to_staff_only)
        parented_problem = modulestore().create_xblock(chapter.runtime, course_key, 'problem', parent_xblock=chapter)
        # FIXME LMS-11376
#         self.assertTrue(parented_problem.visible_to_staff_only)


class TestPublish(SplitModuleTest):
    """
    Test the publishing api
    """
    def setUp(self):
        super(TestPublish, self).setUp()

    def tearDown(self):
        SplitModuleTest.tearDown(self)

    @patch('xmodule.tabs.CourseTab.from_json', side_effect=mock_tab_from_json)
    def test_publish_safe(self, _from_json):
        """
        Test the standard patterns: publish to new branch, revise and publish
        """
        source_course = CourseLocator(org='testx', course='GreekHero', run="run", branch=BRANCH_NAME_DRAFT)
        dest_course = CourseLocator(org='testx', course='GreekHero', run="run", branch=BRANCH_NAME_PUBLISHED)
        head = source_course.make_usage_key('course', "head12345")
        chapter1 = source_course.make_usage_key('chapter', 'chapter1')
        chapter2 = source_course.make_usage_key('chapter', 'chapter2')
        chapter3 = source_course.make_usage_key('chapter', 'chapter3')
        modulestore().copy(self.user_id, source_course, dest_course, [head], [chapter2, chapter3])
        expected = [BlockKey.from_usage_key(head), BlockKey.from_usage_key(chapter1)]
        unexpected = [
            BlockKey.from_usage_key(chapter2),
            BlockKey.from_usage_key(chapter3),
            BlockKey("problem", "problem1"),
            BlockKey("problem", "problem3_2")
        ]
        self._check_course(source_course, dest_course, expected, unexpected)
        # add a child under chapter1
        new_module = modulestore().create_child(
            self.user_id, chapter1, "sequential",
            fields={'display_name': 'new sequential'},
        )
        # remove chapter1 from expected b/c its pub'd version != the source anymore since source changed
        expected.remove(BlockKey.from_usage_key(chapter1))
        # check that it's not in published course
        with self.assertRaises(ItemNotFoundError):
            modulestore().get_item(new_module.location.map_into_course(dest_course))
        # publish it
        modulestore().copy(self.user_id, source_course, dest_course, [new_module.location], None)
        expected.append(BlockKey.from_usage_key(new_module.location))
        # check that it is in the published course and that its parent is the chapter
        pub_module = modulestore().get_item(new_module.location.map_into_course(dest_course))
        self.assertEqual(
            modulestore().get_parent_location(pub_module.location).block_id, chapter1.block_id
        )
        # ensure intentionally orphaned blocks work (e.g., course_info)
        new_module = modulestore().create_item(
            self.user_id, source_course, "course_info", block_id="handouts"
        )
        # publish it
        modulestore().copy(self.user_id, source_course, dest_course, [new_module.location], None)
        expected.append(BlockKey.from_usage_key(new_module.location))
        # check that it is in the published course (no error means it worked)
        pub_module = modulestore().get_item(new_module.location.map_into_course(dest_course))
        self._check_course(source_course, dest_course, expected, unexpected)

    def test_exceptions(self):
        """
        Test the exceptions which preclude successful publication
        """
        source_course = CourseLocator(org='testx', course='GreekHero', run="run", branch=BRANCH_NAME_DRAFT)
        # destination does not exist
        destination_course = CourseLocator(org='fake', course='Unknown', run="run", branch=BRANCH_NAME_PUBLISHED)
        head = source_course.make_usage_key('course', "head12345")
        chapter3 = source_course.make_usage_key('chapter', 'chapter3')
        problem1 = source_course.make_usage_key('problem', 'problem1')
        with self.assertRaises(ItemNotFoundError):
            modulestore().copy(self.user_id, source_course, destination_course, [chapter3], None)
        # publishing into a new branch w/o publishing the root
        destination_course = CourseLocator(org='testx', course='GreekHero', run='run', branch=BRANCH_NAME_PUBLISHED)
        with self.assertRaises(ItemNotFoundError):
            modulestore().copy(self.user_id, source_course, destination_course, [chapter3], None)
        # publishing a subdag w/o the parent already in course
        modulestore().copy(self.user_id, source_course, destination_course, [head], [chapter3])
        with self.assertRaises(ItemNotFoundError):
            modulestore().copy(self.user_id, source_course, destination_course, [problem1], [])

    @patch('xmodule.tabs.CourseTab.from_json', side_effect=mock_tab_from_json)
    def test_move_delete(self, _from_json):
        """
        Test publishing moves and deletes.
        """
        source_course = CourseLocator(org='testx', course='GreekHero', run='run', branch=BRANCH_NAME_DRAFT)
        dest_course = CourseLocator(org='testx', course='GreekHero', run='run', branch=BRANCH_NAME_PUBLISHED)
        head = source_course.make_usage_key('course', "head12345")
        chapter2 = source_course.make_usage_key('chapter', 'chapter2')
        problem1 = source_course.make_usage_key('problem', 'problem1')
        modulestore().copy(self.user_id, source_course, dest_course, [head], [chapter2])
        expected = [
            BlockKey("course", "head12345"),
            BlockKey("chapter", "chapter1"),
            BlockKey("chapter", "chapter3"),
            BlockKey("problem", "problem1"),
            BlockKey("problem", "problem3_2"),
        ]
        self._check_course(source_course, dest_course, expected, [BlockKey("chapter", "chapter2")])
        # now move problem1 and delete problem3_2
        chapter1 = modulestore().get_item(source_course.make_usage_key("chapter", "chapter1"))
        chapter3 = modulestore().get_item(source_course.make_usage_key("chapter", "chapter3"))
        chapter1.children.append(problem1)
        chapter3.children.remove(problem1.map_into_course(chapter3.location.course_key))
        modulestore().delete_item(source_course.make_usage_key("problem", "problem3_2"), self.user_id)
        modulestore().copy(self.user_id, source_course, dest_course, [head], [chapter2])
        expected = [
            BlockKey("course", "head12345"),
            BlockKey("chapter", "chapter1"),
            BlockKey("chapter", "chapter3"),
            BlockKey("problem", "problem1")
        ]
        self._check_course(source_course, dest_course, expected, [BlockKey("chapter", "chapter2"), BlockKey("problem", "problem3_2")])

    @contract(expected_blocks="list(BlockKey)", unexpected_blocks="list(BlockKey)")
    def _check_course(self, source_course_loc, dest_course_loc, expected_blocks, unexpected_blocks):
        """
        Check that the course has the expected blocks and does not have the unexpected blocks
        """
        history_info = modulestore().get_course_history_info(dest_course_loc)
        self.assertEqual(history_info['edited_by'], self.user_id)
        for expected in expected_blocks:
            source = modulestore().get_item(source_course_loc.make_usage_key(expected.type, expected.id))
            pub_copy = modulestore().get_item(dest_course_loc.make_usage_key(expected.type, expected.id))
            # everything except previous_version & children should be the same
            self.assertEqual(source.category, pub_copy.category)
            self.assertEqual(
                source.update_version, pub_copy.source_version,
                u"Versions don't match for {}: {} != {}".format(
                    expected, source.update_version, pub_copy.update_version
                )
            )
            self.assertEqual(
                self.user_id, pub_copy.edited_by,
                "{} edited_by {} not {}".format(pub_copy.location, pub_copy.edited_by, self.user_id)
            )
            for field in source.fields.values():
                if field.name == 'children':
                    self._compare_children(field.read_from(source), field.read_from(pub_copy), unexpected_blocks)
                elif isinstance(field, (Reference, ReferenceList, ReferenceValueDict)):
                    self.assertReferenceEqual(field.read_from(source), field.read_from(pub_copy))
                else:
                    self.assertEqual(field.read_from(source), field.read_from(pub_copy))
        for unexp in unexpected_blocks:
            with self.assertRaises(ItemNotFoundError):
                modulestore().get_item(dest_course_loc.make_usage_key(unexp.type, unexp.id))

    def assertReferenceEqual(self, expected, actual):
        if isinstance(expected, BlockUsageLocator):
            expected = BlockKey.from_usage_key(expected)
            actual = BlockKey.from_usage_key(actual)
        elif isinstance(expected, list):
            expected = [BlockKey.from_usage_key(key) for key in expected]
            actual = [BlockKey.from_usage_key(key) for key in actual]
        elif isinstance(expected, dict):
            expected = {key: BlockKey.from_usage_key(val) for (key, val) in expected}
            actual = {key: BlockKey.from_usage_key(val) for (key, val) in actual}
        self.assertEqual(expected, actual)

    @contract(
        source_children="list(BlockUsageLocator)",
        dest_children="list(BlockUsageLocator)",
        unexpected="list(BlockKey)"
    )
    def _compare_children(self, source_children, dest_children, unexpected):
        """
        Ensure dest_children == source_children minus unexpected
        """
        source_block_keys = [
            src_key
            for src_key
            in (BlockKey.from_usage_key(src) for src in source_children)
            if src_key not in unexpected
        ]
        dest_block_keys = [BlockKey.from_usage_key(dest) for dest in dest_children]
        for unexp in unexpected:
            self.assertNotIn(unexp, dest_block_keys)

        self.assertEqual(source_block_keys, dest_block_keys)


class TestSchema(SplitModuleTest):
    """
    Test the db schema (and possibly eventually migrations?)
    """
    def test_schema(self):
        """
        Test that the schema is set in each document
        """
        db_connection = modulestore().db_connection
        for collection in [db_connection.course_index, db_connection.structures, db_connection.definitions]:
            self.assertEqual(
                collection.find({'schema_version': {'$exists': False}}).count(),
                0,
                "{0.name} has records without schema_version".format(collection)
            )
            self.assertEqual(
                collection.find({'schema_version': {'$ne': SplitMongoModuleStore.SCHEMA_VERSION}}).count(),
                0,
                "{0.name} has records with wrong schema_version".format(collection)
            )


# ===========================================
def modulestore():
    """
    Mock the django dependent global modulestore function to disentangle tests from django
    """
    def load_function(engine_path):
        """
        Load the given engine
        """
        module_path, _, name = engine_path.rpartition('.')
        return getattr(import_module(module_path), name)

    if SplitModuleTest.modulestore is None:
        class_ = load_function(SplitModuleTest.MODULESTORE['ENGINE'])

        options = {}

        options.update(SplitModuleTest.MODULESTORE['OPTIONS'])
        options['render_template'] = render_to_template_mock

        # pylint: disable=star-args
        SplitModuleTest.modulestore = class_(
            None,  # contentstore
            SplitModuleTest.MODULESTORE['DOC_STORE_CONFIG'],
            **options
        )

        SplitModuleTest.bootstrapDB(SplitModuleTest.modulestore)

    return SplitModuleTest.modulestore


# pylint: disable=unused-argument, missing-docstring
def render_to_template_mock(*args):
    pass
