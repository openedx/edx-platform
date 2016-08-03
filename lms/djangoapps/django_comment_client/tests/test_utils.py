# -*- coding: utf-8 -*-
import datetime
import json
import ddt
import mock
from nose.plugins.attrib import attr
from pytz import UTC
from django.utils.timezone import UTC as django_utc

from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory
from edxmako import add_lookup

from django_comment_client.tests.factories import RoleFactory
from django_comment_client.tests.unicode import UnicodeTestMixin
import django_comment_client.utils as utils

from courseware.tests.factories import InstructorFactory
from courseware.tabs import get_course_tab_list
from openedx.core.djangoapps.course_groups import cohorts
from openedx.core.djangoapps.course_groups.cohorts import set_course_cohort_settings
from openedx.core.djangoapps.course_groups.tests.helpers import config_course_cohorts, topic_name_to_id
from student.tests.factories import UserFactory, AdminFactory, CourseEnrollmentFactory
from openedx.core.djangoapps.content.course_structures.models import CourseStructure
from openedx.core.djangoapps.util.testing import ContentGroupTestCase
from student.roles import CourseStaffRole
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, ToyCourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, TEST_DATA_MIXED_MODULESTORE
from xmodule.modulestore.django import modulestore
from lms.djangoapps.teams.tests.factories import CourseTeamFactory


@attr('shard_1')
class DictionaryTestCase(TestCase):
    def test_extract(self):
        d = {'cats': 'meow', 'dogs': 'woof'}
        k = ['cats', 'dogs', 'hamsters']
        expected = {'cats': 'meow', 'dogs': 'woof', 'hamsters': None}
        self.assertEqual(utils.extract(d, k), expected)

    def test_strip_none(self):
        d = {'cats': 'meow', 'dogs': 'woof', 'hamsters': None}
        expected = {'cats': 'meow', 'dogs': 'woof'}
        self.assertEqual(utils.strip_none(d), expected)

    def test_strip_blank(self):
        d = {'cats': 'meow', 'dogs': 'woof', 'hamsters': ' ', 'yetis': ''}
        expected = {'cats': 'meow', 'dogs': 'woof'}
        self.assertEqual(utils.strip_blank(d), expected)

    def test_merge_dict(self):
        d1 = {'cats': 'meow', 'dogs': 'woof'}
        d2 = {'lions': 'roar', 'ducks': 'quack'}
        expected = {'cats': 'meow', 'dogs': 'woof', 'lions': 'roar', 'ducks': 'quack'}
        self.assertEqual(utils.merge_dict(d1, d2), expected)


@attr('shard_1')
class AccessUtilsTestCase(ModuleStoreTestCase):
    """
    Base testcase class for access and roles for the
    comment client service integration
    """
    CREATE_USER = False

    def setUp(self):
        super(AccessUtilsTestCase, self).setUp()

        self.course = CourseFactory.create()
        self.course_id = self.course.id
        self.student_role = RoleFactory(name='Student', course_id=self.course_id)
        self.moderator_role = RoleFactory(name='Moderator', course_id=self.course_id)
        self.community_ta_role = RoleFactory(name='Community TA', course_id=self.course_id)
        self.student1 = UserFactory(username='student', email='student@edx.org')
        self.student1_enrollment = CourseEnrollmentFactory(user=self.student1)
        self.student_role.users.add(self.student1)
        self.student2 = UserFactory(username='student2', email='student2@edx.org')
        self.student2_enrollment = CourseEnrollmentFactory(user=self.student2)
        self.moderator = UserFactory(username='moderator', email='staff@edx.org', is_staff=True)
        self.moderator_enrollment = CourseEnrollmentFactory(user=self.moderator)
        self.moderator_role.users.add(self.moderator)
        self.community_ta1 = UserFactory(username='community_ta1', email='community_ta1@edx.org')
        self.community_ta_role.users.add(self.community_ta1)
        self.community_ta2 = UserFactory(username='community_ta2', email='community_ta2@edx.org')
        self.community_ta_role.users.add(self.community_ta2)
        self.course_staff = UserFactory(username='course_staff', email='course_staff@edx.org')
        CourseStaffRole(self.course_id).add_users(self.course_staff)

    def test_get_role_ids(self):
        ret = utils.get_role_ids(self.course_id)
        expected = {u'Moderator': [3], u'Community TA': [4, 5]}
        self.assertEqual(ret, expected)

    def test_has_discussion_privileges(self):
        self.assertFalse(utils.has_discussion_privileges(self.student1, self.course_id))
        self.assertFalse(utils.has_discussion_privileges(self.student2, self.course_id))
        self.assertFalse(utils.has_discussion_privileges(self.course_staff, self.course_id))
        self.assertTrue(utils.has_discussion_privileges(self.moderator, self.course_id))
        self.assertTrue(utils.has_discussion_privileges(self.community_ta1, self.course_id))
        self.assertTrue(utils.has_discussion_privileges(self.community_ta2, self.course_id))

    def test_has_forum_access(self):
        ret = utils.has_forum_access('student', self.course_id, 'Student')
        self.assertTrue(ret)

        ret = utils.has_forum_access('not_a_student', self.course_id, 'Student')
        self.assertFalse(ret)

        ret = utils.has_forum_access('student', self.course_id, 'NotARole')
        self.assertFalse(ret)


@ddt.ddt
@attr('shard_1')
class CoursewareContextTestCase(ModuleStoreTestCase):
    """
    Base testcase class for courseware context for the
    comment client service integration
    """
    def setUp(self):
        super(CoursewareContextTestCase, self).setUp()

        self.course = CourseFactory.create(org="TestX", number="101", display_name="Test Course")
        self.discussion1 = ItemFactory.create(
            parent_location=self.course.location,
            category="discussion",
            discussion_id="discussion1",
            discussion_category="Chapter",
            discussion_target="Discussion 1"
        )
        self.discussion2 = ItemFactory.create(
            parent_location=self.course.location,
            category="discussion",
            discussion_id="discussion2",
            discussion_category="Chapter / Section / Subsection",
            discussion_target="Discussion 2"
        )

    def test_empty(self):
        utils.add_courseware_context([], self.course, self.user)

    def test_missing_commentable_id(self):
        orig = {"commentable_id": "non-inline"}
        modified = dict(orig)
        utils.add_courseware_context([modified], self.course, self.user)
        self.assertEqual(modified, orig)

    def test_basic(self):
        threads = [
            {"commentable_id": self.discussion1.discussion_id},
            {"commentable_id": self.discussion2.discussion_id}
        ]
        utils.add_courseware_context(threads, self.course, self.user)

        def assertThreadCorrect(thread, discussion, expected_title):  # pylint: disable=invalid-name
            """Asserts that the given thread has the expected set of properties"""
            self.assertEqual(
                set(thread.keys()),
                set(["commentable_id", "courseware_url", "courseware_title"])
            )
            self.assertEqual(
                thread.get("courseware_url"),
                reverse(
                    "jump_to",
                    kwargs={
                        "course_id": self.course.id.to_deprecated_string(),
                        "location": discussion.location.to_deprecated_string()
                    }
                )
            )
            self.assertEqual(thread.get("courseware_title"), expected_title)

        assertThreadCorrect(threads[0], self.discussion1, "Chapter / Discussion 1")
        assertThreadCorrect(threads[1], self.discussion2, "Subsection / Discussion 2")

    @ddt.data((ModuleStoreEnum.Type.mongo, 2), (ModuleStoreEnum.Type.split, 1))
    @ddt.unpack
    def test_get_accessible_discussion_xblocks(self, modulestore_type, expected_discussion_xblocks):
        """
        Tests that the accessible discussion xblocks having no parents do not get fetched for split modulestore.
        """
        course = CourseFactory.create(default_store=modulestore_type)

        # Create a discussion xblock.
        test_discussion = self.store.create_child(self.user.id, course.location, 'discussion', 'test_discussion')

        # Assert that created discussion xblock is not an orphan.
        self.assertNotIn(test_discussion.location, self.store.get_orphans(course.id))

        # Assert that there is only one discussion xblock in the course at the moment.
        self.assertEqual(len(utils.get_accessible_discussion_xblocks(course, self.user)), 1)

        # Add an orphan discussion xblock to that course
        orphan = course.id.make_usage_key('discussion', 'orphan_discussion')
        self.store.create_item(self.user.id, orphan.course_key, orphan.block_type, block_id=orphan.block_id)

        # Assert that the discussion xblock is an orphan.
        self.assertIn(orphan, self.store.get_orphans(course.id))

        self.assertEqual(len(utils.get_accessible_discussion_xblocks(course, self.user)), expected_discussion_xblocks)


@attr('shard_3')
class CachedDiscussionIdMapTestCase(ModuleStoreTestCase):
    """
    Tests that using the cache of discussion id mappings has the same behavior as searching through the course.
    """
    def setUp(self):
        super(CachedDiscussionIdMapTestCase, self).setUp()

        self.course = CourseFactory.create(org='TestX', number='101', display_name='Test Course')
        self.discussion = ItemFactory.create(
            parent_location=self.course.location,
            category='discussion',
            discussion_id='test_discussion_id',
            discussion_category='Chapter',
            discussion_target='Discussion 1'
        )
        self.discussion2 = ItemFactory.create(
            parent_location=self.course.location,
            category='discussion',
            discussion_id='test_discussion_id_2',
            discussion_category='Chapter 2',
            discussion_target='Discussion 2'
        )
        self.private_discussion = ItemFactory.create(
            parent_location=self.course.location,
            category='discussion',
            discussion_id='private_discussion_id',
            discussion_category='Chapter 3',
            discussion_target='Beta Testing',
            visible_to_staff_only=True
        )
        self.bad_discussion = ItemFactory.create(
            parent_location=self.course.location,
            category='discussion',
            discussion_id='bad_discussion_id',
            discussion_category=None,
            discussion_target=None
        )

    def test_cache_returns_correct_key(self):
        usage_key = utils.get_cached_discussion_key(self.course, 'test_discussion_id')
        self.assertEqual(usage_key, self.discussion.location)

    def test_cache_returns_none_if_id_is_not_present(self):
        usage_key = utils.get_cached_discussion_key(self.course, 'bogus_id')
        self.assertIsNone(usage_key)

    def test_cache_raises_exception_if_course_structure_not_cached(self):
        CourseStructure.objects.all().delete()
        with self.assertRaises(utils.DiscussionIdMapIsNotCached):
            utils.get_cached_discussion_key(self.course, 'test_discussion_id')

    def test_cache_raises_exception_if_discussion_id_not_cached(self):
        cache = CourseStructure.objects.get(course_id=self.course.id)
        cache.discussion_id_map_json = None
        cache.save()

        with self.assertRaises(utils.DiscussionIdMapIsNotCached):
            utils.get_cached_discussion_key(self.course, 'test_discussion_id')

    def test_xblock_does_not_have_required_keys(self):
        self.assertTrue(utils.has_required_keys(self.discussion))
        self.assertFalse(utils.has_required_keys(self.bad_discussion))

    def verify_discussion_metadata(self):
        """Retrieves the metadata for self.discussion and self.discussion2 and verifies that it is correct"""
        metadata = utils.get_cached_discussion_id_map(
            self.course,
            ['test_discussion_id', 'test_discussion_id_2'],
            self.user
        )
        discussion1 = metadata[self.discussion.discussion_id]
        discussion2 = metadata[self.discussion2.discussion_id]
        self.assertEqual(discussion1['location'], self.discussion.location)
        self.assertEqual(discussion1['title'], 'Chapter / Discussion 1')
        self.assertEqual(discussion2['location'], self.discussion2.location)
        self.assertEqual(discussion2['title'], 'Chapter 2 / Discussion 2')

    def test_get_discussion_id_map_from_cache(self):
        self.verify_discussion_metadata()

    def test_get_discussion_id_map_without_cache(self):
        CourseStructure.objects.all().delete()
        self.verify_discussion_metadata()

    def test_get_missing_discussion_id_map_from_cache(self):
        metadata = utils.get_cached_discussion_id_map(self.course, ['bogus_id'], self.user)
        self.assertEqual(metadata, {})

    def test_get_discussion_id_map_from_cache_without_access(self):
        user = UserFactory.create()

        metadata = utils.get_cached_discussion_id_map(self.course, ['private_discussion_id'], self.user)
        self.assertEqual(metadata['private_discussion_id']['title'], 'Chapter 3 / Beta Testing')

        metadata = utils.get_cached_discussion_id_map(self.course, ['private_discussion_id'], user)
        self.assertEqual(metadata, {})

    def test_get_bad_discussion_id(self):
        metadata = utils.get_cached_discussion_id_map(self.course, ['bad_discussion_id'], self.user)
        self.assertEqual(metadata, {})

    def test_discussion_id_accessible(self):
        self.assertTrue(utils.discussion_category_id_access(self.course, self.user, 'test_discussion_id'))

    def test_bad_discussion_id_not_accessible(self):
        self.assertFalse(utils.discussion_category_id_access(self.course, self.user, 'bad_discussion_id'))

    def test_missing_discussion_id_not_accessible(self):
        self.assertFalse(utils.discussion_category_id_access(self.course, self.user, 'bogus_id'))

    def test_discussion_id_not_accessible_without_access(self):
        user = UserFactory.create()
        self.assertTrue(utils.discussion_category_id_access(self.course, self.user, 'private_discussion_id'))
        self.assertFalse(utils.discussion_category_id_access(self.course, user, 'private_discussion_id'))


class CategoryMapTestMixin(object):
    """
    Provides functionality for classes that test
    `get_discussion_category_map`.
    """
    def assert_category_map_equals(self, expected, requesting_user=None):
        """
        Call `get_discussion_category_map`, and verify that it returns
        what is expected.
        """
        self.assertEqual(
            utils.get_discussion_category_map(self.course, requesting_user or self.user),
            expected
        )


@attr('shard_1')
class CategoryMapTestCase(CategoryMapTestMixin, ModuleStoreTestCase):
    """
    Base testcase class for discussion categories for the
    comment client service integration
    """
    def setUp(self):
        super(CategoryMapTestCase, self).setUp()

        self.course = CourseFactory.create(
            org="TestX", number="101", display_name="Test Course",
            # This test needs to use a course that has already started --
            # discussion topics only show up if the course has already started,
            # and the default start date for courses is Jan 1, 2030.
            start=datetime.datetime(2012, 2, 3, tzinfo=UTC)
        )
        # Courses get a default discussion topic on creation, so remove it
        self.course.discussion_topics = {}
        self.course.save()
        self.discussion_num = 0
        self.instructor = InstructorFactory(course_key=self.course.id)
        self.maxDiff = None  # pylint: disable=invalid-name

    def create_discussion(self, discussion_category, discussion_target, **kwargs):
        self.discussion_num += 1
        return ItemFactory.create(
            parent_location=self.course.location,
            category="discussion",
            discussion_id="discussion{}".format(self.discussion_num),
            discussion_category=discussion_category,
            discussion_target=discussion_target,
            **kwargs
        )

    def assert_category_map_equals(self, expected, cohorted_if_in_list=False, exclude_unstarted=True):  # pylint: disable=arguments-differ
        """
        Asserts the expected map with the map returned by get_discussion_category_map method.
        """
        self.assertEqual(
            utils.get_discussion_category_map(self.course, self.instructor, cohorted_if_in_list, exclude_unstarted),
            expected
        )

    def test_empty(self):
        self.assert_category_map_equals({"entries": {}, "subcategories": {}, "children": []})

    def test_configured_topics(self):
        self.course.discussion_topics = {
            "Topic A": {"id": "Topic_A"},
            "Topic B": {"id": "Topic_B"},
            "Topic C": {"id": "Topic_C"}
        }

        def check_cohorted_topics(expected_ids):  # pylint: disable=missing-docstring
            self.assert_category_map_equals(
                {
                    "entries": {
                        "Topic A": {"id": "Topic_A", "sort_key": "Topic A", "is_cohorted": "Topic_A" in expected_ids},
                        "Topic B": {"id": "Topic_B", "sort_key": "Topic B", "is_cohorted": "Topic_B" in expected_ids},
                        "Topic C": {"id": "Topic_C", "sort_key": "Topic C", "is_cohorted": "Topic_C" in expected_ids},
                    },
                    "subcategories": {},
                    "children": ["Topic A", "Topic B", "Topic C"]
                }
            )

        check_cohorted_topics([])  # default (empty) cohort config

        set_course_cohort_settings(course_key=self.course.id, is_cohorted=False, cohorted_discussions=[])
        check_cohorted_topics([])

        set_course_cohort_settings(course_key=self.course.id, is_cohorted=True, cohorted_discussions=[])
        check_cohorted_topics([])

        set_course_cohort_settings(
            course_key=self.course.id,
            is_cohorted=True,
            cohorted_discussions=["Topic_B", "Topic_C"],
            always_cohort_inline_discussions=False,
        )
        check_cohorted_topics(["Topic_B", "Topic_C"])

        set_course_cohort_settings(
            course_key=self.course.id,
            is_cohorted=True,
            cohorted_discussions=["Topic_A", "Some_Other_Topic"],
            always_cohort_inline_discussions=False,
        )
        check_cohorted_topics(["Topic_A"])

        # unlikely case, but make sure it works.
        set_course_cohort_settings(
            course_key=self.course.id,
            is_cohorted=False,
            cohorted_discussions=["Topic_A"],
            always_cohort_inline_discussions=False,
        )
        check_cohorted_topics([])

    def test_single_inline(self):
        self.create_discussion("Chapter", "Discussion")
        self.assert_category_map_equals(
            {
                "entries": {},
                "subcategories": {
                    "Chapter": {
                        "entries": {
                            "Discussion": {
                                "id": "discussion1",
                                "sort_key": None,
                                "is_cohorted": False,
                            }
                        },
                        "subcategories": {},
                        "children": ["Discussion"]
                    }
                },
                "children": ["Chapter"]
            }
        )

    def test_inline_with_always_cohort_inline_discussion_flag(self):
        self.create_discussion("Chapter", "Discussion")
        set_course_cohort_settings(course_key=self.course.id, is_cohorted=True)

        self.assert_category_map_equals(
            {
                "entries": {},
                "subcategories": {
                    "Chapter": {
                        "entries": {
                            "Discussion": {
                                "id": "discussion1",
                                "sort_key": None,
                                "is_cohorted": True,
                            }
                        },
                        "subcategories": {},
                        "children": ["Discussion"]
                    }
                },
                "children": ["Chapter"]
            }
        )

    def test_inline_without_always_cohort_inline_discussion_flag(self):
        self.create_discussion("Chapter", "Discussion")
        set_course_cohort_settings(course_key=self.course.id, is_cohorted=True, always_cohort_inline_discussions=False)

        self.assert_category_map_equals(
            {
                "entries": {},
                "subcategories": {
                    "Chapter": {
                        "entries": {
                            "Discussion": {
                                "id": "discussion1",
                                "sort_key": None,
                                "is_cohorted": False,
                            }
                        },
                        "subcategories": {},
                        "children": ["Discussion"]
                    }
                },
                "children": ["Chapter"]
            },
            cohorted_if_in_list=True
        )

    def test_get_unstarted_discussion_xblocks(self):
        later = datetime.datetime(datetime.MAXYEAR, 1, 1, tzinfo=django_utc())

        self.create_discussion("Chapter 1", "Discussion 1", start=later)

        self.assert_category_map_equals(
            {
                "entries": {},
                "subcategories": {
                    "Chapter 1": {
                        "entries": {
                            "Discussion 1": {
                                "id": "discussion1",
                                "sort_key": None,
                                "is_cohorted": False,
                                "start_date": later
                            }
                        },
                        "subcategories": {},
                        "children": ["Discussion 1"],
                        "start_date": later,
                        "sort_key": "Chapter 1"
                    }
                },
                "children": ["Chapter 1"]
            },
            cohorted_if_in_list=True,
            exclude_unstarted=False
        )

    def test_tree(self):
        self.create_discussion("Chapter 1", "Discussion 1")
        self.create_discussion("Chapter 1", "Discussion 2")
        self.create_discussion("Chapter 2", "Discussion")
        self.create_discussion("Chapter 2 / Section 1 / Subsection 1", "Discussion")
        self.create_discussion("Chapter 2 / Section 1 / Subsection 2", "Discussion")
        self.create_discussion("Chapter 3 / Section 1", "Discussion")

        def check_cohorted(is_cohorted):

            self.assert_category_map_equals(
                {
                    "entries": {},
                    "subcategories": {
                        "Chapter 1": {
                            "entries": {
                                "Discussion 1": {
                                    "id": "discussion1",
                                    "sort_key": None,
                                    "is_cohorted": is_cohorted,
                                },
                                "Discussion 2": {
                                    "id": "discussion2",
                                    "sort_key": None,
                                    "is_cohorted": is_cohorted,
                                }
                            },
                            "subcategories": {},
                            "children": ["Discussion 1", "Discussion 2"]
                        },
                        "Chapter 2": {
                            "entries": {
                                "Discussion": {
                                    "id": "discussion3",
                                    "sort_key": None,
                                    "is_cohorted": is_cohorted,
                                }
                            },
                            "subcategories": {
                                "Section 1": {
                                    "entries": {},
                                    "subcategories": {
                                        "Subsection 1": {
                                            "entries": {
                                                "Discussion": {
                                                    "id": "discussion4",
                                                    "sort_key": None,
                                                    "is_cohorted": is_cohorted,
                                                }
                                            },
                                            "subcategories": {},
                                            "children": ["Discussion"]
                                        },
                                        "Subsection 2": {
                                            "entries": {
                                                "Discussion": {
                                                    "id": "discussion5",
                                                    "sort_key": None,
                                                    "is_cohorted": is_cohorted,
                                                }
                                            },
                                            "subcategories": {},
                                            "children": ["Discussion"]
                                        }
                                    },
                                    "children": ["Subsection 1", "Subsection 2"]
                                }
                            },
                            "children": ["Discussion", "Section 1"]
                        },
                        "Chapter 3": {
                            "entries": {},
                            "subcategories": {
                                "Section 1": {
                                    "entries": {
                                        "Discussion": {
                                            "id": "discussion6",
                                            "sort_key": None,
                                            "is_cohorted": is_cohorted,
                                        }
                                    },
                                    "subcategories": {},
                                    "children": ["Discussion"]
                                }
                            },
                            "children": ["Section 1"]
                        }
                    },
                    "children": ["Chapter 1", "Chapter 2", "Chapter 3"]
                }
            )

        # empty / default config
        check_cohorted(False)

        # explicitly disabled cohorting
        set_course_cohort_settings(course_key=self.course.id, is_cohorted=False)
        check_cohorted(False)

        # explicitly enabled cohorting
        set_course_cohort_settings(course_key=self.course.id, is_cohorted=True)
        check_cohorted(True)

    def test_tree_with_duplicate_targets(self):
        self.create_discussion("Chapter 1", "Discussion A")
        self.create_discussion("Chapter 1", "Discussion B")
        self.create_discussion("Chapter 1", "Discussion A")  # duplicate
        self.create_discussion("Chapter 1", "Discussion A")  # another duplicate
        self.create_discussion("Chapter 2 / Section 1 / Subsection 1", "Discussion")
        self.create_discussion("Chapter 2 / Section 1 / Subsection 1", "Discussion")  # duplicate

        category_map = utils.get_discussion_category_map(self.course, self.user)

        chapter1 = category_map["subcategories"]["Chapter 1"]
        chapter1_discussions = set(["Discussion A", "Discussion B", "Discussion A (1)", "Discussion A (2)"])
        self.assertEqual(set(chapter1["children"]), chapter1_discussions)
        self.assertEqual(set(chapter1["entries"].keys()), chapter1_discussions)

        chapter2 = category_map["subcategories"]["Chapter 2"]
        subsection1 = chapter2["subcategories"]["Section 1"]["subcategories"]["Subsection 1"]
        subsection1_discussions = set(["Discussion", "Discussion (1)"])
        self.assertEqual(set(subsection1["children"]), subsection1_discussions)
        self.assertEqual(set(subsection1["entries"].keys()), subsection1_discussions)

    def test_start_date_filter(self):
        now = datetime.datetime.now()
        later = datetime.datetime.max
        self.create_discussion("Chapter 1", "Discussion 1", start=now)
        self.create_discussion("Chapter 1", "Discussion 2 обсуждение", start=later)
        self.create_discussion("Chapter 2", "Discussion", start=now)
        self.create_discussion("Chapter 2 / Section 1 / Subsection 1", "Discussion", start=later)
        self.create_discussion("Chapter 2 / Section 1 / Subsection 2", "Discussion", start=later)
        self.create_discussion("Chapter 3 / Section 1", "Discussion", start=later)

        self.assertFalse(self.course.self_paced)
        self.assert_category_map_equals(
            {
                "entries": {},
                "subcategories": {
                    "Chapter 1": {
                        "entries": {
                            "Discussion 1": {
                                "id": "discussion1",
                                "sort_key": None,
                                "is_cohorted": False,
                            }
                        },
                        "subcategories": {},
                        "children": ["Discussion 1"]
                    },
                    "Chapter 2": {
                        "entries": {
                            "Discussion": {
                                "id": "discussion3",
                                "sort_key": None,
                                "is_cohorted": False,
                            }
                        },
                        "subcategories": {},
                        "children": ["Discussion"]
                    }
                },
                "children": ["Chapter 1", "Chapter 2"]
            }
        )

    def test_self_paced_start_date_filter(self):
        self.course.self_paced = True
        self.course.save()

        now = datetime.datetime.now()
        later = datetime.datetime.max
        self.create_discussion("Chapter 1", "Discussion 1", start=now)
        self.create_discussion("Chapter 1", "Discussion 2", start=later)
        self.create_discussion("Chapter 2", "Discussion", start=now)
        self.create_discussion("Chapter 2 / Section 1 / Subsection 1", "Discussion", start=later)
        self.create_discussion("Chapter 2 / Section 1 / Subsection 2", "Discussion", start=later)
        self.create_discussion("Chapter 3 / Section 1", "Discussion", start=later)

        self.assertTrue(self.course.self_paced)
        self.assert_category_map_equals(
            {
                "entries": {},
                "subcategories": {
                    "Chapter 1": {
                        "entries": {
                            "Discussion 1": {
                                "id": "discussion1",
                                "sort_key": None,
                                "is_cohorted": False,
                            },
                            "Discussion 2": {
                                "id": "discussion2",
                                "sort_key": None,
                                "is_cohorted": False,
                            }
                        },
                        "subcategories": {},
                        "children": ["Discussion 1", "Discussion 2"]
                    },
                    "Chapter 2": {
                        "entries": {
                            "Discussion": {
                                "id": "discussion3",
                                "sort_key": None,
                                "is_cohorted": False,
                            }
                        },
                        "subcategories": {
                            "Section 1": {
                                "entries": {},
                                "subcategories": {
                                    "Subsection 1": {
                                        "entries": {
                                            "Discussion": {
                                                "id": "discussion4",
                                                "sort_key": None,
                                                "is_cohorted": False,
                                            }
                                        },
                                        "subcategories": {},
                                        "children": ["Discussion"]
                                    },
                                    "Subsection 2": {
                                        "entries": {
                                            "Discussion": {
                                                "id": "discussion5",
                                                "sort_key": None,
                                                "is_cohorted": False,
                                            }
                                        },
                                        "subcategories": {},
                                        "children": ["Discussion"]
                                    }
                                },
                                "children": ["Subsection 1", "Subsection 2"]
                            }
                        },
                        "children": ["Discussion", "Section 1"]
                    },
                    "Chapter 3": {
                        "entries": {},
                        "subcategories": {
                            "Section 1": {
                                "entries": {
                                    "Discussion": {
                                        "id": "discussion6",
                                        "sort_key": None,
                                        "is_cohorted": False,
                                    }
                                },
                                "subcategories": {},
                                "children": ["Discussion"]
                            }
                        },
                        "children": ["Section 1"]
                    }
                },
                "children": ["Chapter 1", "Chapter 2", "Chapter 3"]
            }
        )

    def test_sort_inline_explicit(self):
        self.create_discussion("Chapter", "Discussion 1", sort_key="D")
        self.create_discussion("Chapter", "Discussion 2", sort_key="A")
        self.create_discussion("Chapter", "Discussion 3", sort_key="E")
        self.create_discussion("Chapter", "Discussion 4", sort_key="C")
        self.create_discussion("Chapter", "Discussion 5", sort_key="B")

        self.assert_category_map_equals(
            {
                "entries": {},
                "subcategories": {
                    "Chapter": {
                        "entries": {
                            "Discussion 1": {
                                "id": "discussion1",
                                "sort_key": "D",
                                "is_cohorted": False,
                            },
                            "Discussion 2": {
                                "id": "discussion2",
                                "sort_key": "A",
                                "is_cohorted": False,
                            },
                            "Discussion 3": {
                                "id": "discussion3",
                                "sort_key": "E",
                                "is_cohorted": False,
                            },
                            "Discussion 4": {
                                "id": "discussion4",
                                "sort_key": "C",
                                "is_cohorted": False,
                            },
                            "Discussion 5": {
                                "id": "discussion5",
                                "sort_key": "B",
                                "is_cohorted": False,
                            }
                        },
                        "subcategories": {},
                        "children": [
                            "Discussion 2",
                            "Discussion 5",
                            "Discussion 4",
                            "Discussion 1",
                            "Discussion 3"
                        ]
                    }
                },
                "children": ["Chapter"]
            }
        )

    def test_sort_configured_topics_explicit(self):
        self.course.discussion_topics = {
            "Topic A": {"id": "Topic_A", "sort_key": "B"},
            "Topic B": {"id": "Topic_B", "sort_key": "C"},
            "Topic C": {"id": "Topic_C", "sort_key": "A"}
        }
        self.assert_category_map_equals(
            {
                "entries": {
                    "Topic A": {"id": "Topic_A", "sort_key": "B", "is_cohorted": False},
                    "Topic B": {"id": "Topic_B", "sort_key": "C", "is_cohorted": False},
                    "Topic C": {"id": "Topic_C", "sort_key": "A", "is_cohorted": False},
                },
                "subcategories": {},
                "children": ["Topic C", "Topic A", "Topic B"]
            }
        )

    def test_sort_alpha(self):
        self.course.discussion_sort_alpha = True
        self.course.save()
        self.create_discussion("Chapter", "Discussion D")
        self.create_discussion("Chapter", "Discussion A")
        self.create_discussion("Chapter", "Discussion E")
        self.create_discussion("Chapter", "Discussion C")
        self.create_discussion("Chapter", "Discussion B")

        self.assert_category_map_equals(
            {
                "entries": {},
                "subcategories": {
                    "Chapter": {
                        "entries": {
                            "Discussion D": {
                                "id": "discussion1",
                                "sort_key": "Discussion D",
                                "is_cohorted": False,
                            },
                            "Discussion A": {
                                "id": "discussion2",
                                "sort_key": "Discussion A",
                                "is_cohorted": False,
                            },
                            "Discussion E": {
                                "id": "discussion3",
                                "sort_key": "Discussion E",
                                "is_cohorted": False,
                            },
                            "Discussion C": {
                                "id": "discussion4",
                                "sort_key": "Discussion C",
                                "is_cohorted": False,
                            },
                            "Discussion B": {
                                "id": "discussion5",
                                "sort_key": "Discussion B",
                                "is_cohorted": False,
                            }
                        },
                        "subcategories": {},
                        "children": [
                            "Discussion A",
                            "Discussion B",
                            "Discussion C",
                            "Discussion D",
                            "Discussion E"
                        ]
                    }
                },
                "children": ["Chapter"]
            }
        )

    def test_sort_intermediates(self):
        self.create_discussion("Chapter B", "Discussion 2")
        self.create_discussion("Chapter C", "Discussion")
        self.create_discussion("Chapter A", "Discussion 1")
        self.create_discussion("Chapter B", "Discussion 1")
        self.create_discussion("Chapter A", "Discussion 2")

        self.assert_category_map_equals(
            {
                "entries": {},
                "subcategories": {
                    "Chapter A": {
                        "entries": {
                            "Discussion 1": {
                                "id": "discussion3",
                                "sort_key": None,
                                "is_cohorted": False,
                            },
                            "Discussion 2": {
                                "id": "discussion5",
                                "sort_key": None,
                                "is_cohorted": False,
                            }
                        },
                        "subcategories": {},
                        "children": ["Discussion 1", "Discussion 2"]
                    },
                    "Chapter B": {
                        "entries": {
                            "Discussion 1": {
                                "id": "discussion4",
                                "sort_key": None,
                                "is_cohorted": False,
                            },
                            "Discussion 2": {
                                "id": "discussion1",
                                "sort_key": None,
                                "is_cohorted": False,
                            }
                        },
                        "subcategories": {},
                        "children": ["Discussion 1", "Discussion 2"]
                    },
                    "Chapter C": {
                        "entries": {
                            "Discussion": {
                                "id": "discussion2",
                                "sort_key": None,
                                "is_cohorted": False,
                            }
                        },
                        "subcategories": {},
                        "children": ["Discussion"]
                    }
                },
                "children": ["Chapter A", "Chapter B", "Chapter C"]
            }
        )

    def test_ids_empty(self):
        self.assertEqual(utils.get_discussion_categories_ids(self.course, self.user), [])

    def test_ids_configured_topics(self):
        self.course.discussion_topics = {
            "Topic A": {"id": "Topic_A"},
            "Topic B": {"id": "Topic_B"},
            "Topic C": {"id": "Topic_C"}
        }
        self.assertItemsEqual(
            utils.get_discussion_categories_ids(self.course, self.user),
            ["Topic_A", "Topic_B", "Topic_C"]
        )

    def test_ids_inline(self):
        self.create_discussion("Chapter 1", "Discussion 1")
        self.create_discussion("Chapter 1", "Discussion 2")
        self.create_discussion("Chapter 2", "Discussion")
        self.create_discussion("Chapter 2 / Section 1 / Subsection 1", "Discussion")
        self.create_discussion("Chapter 2 / Section 1 / Subsection 2", "Discussion")
        self.create_discussion("Chapter 3 / Section 1", "Discussion")
        self.assertItemsEqual(
            utils.get_discussion_categories_ids(self.course, self.user),
            ["discussion1", "discussion2", "discussion3", "discussion4", "discussion5", "discussion6"]
        )

    def test_ids_mixed(self):
        self.course.discussion_topics = {
            "Topic A": {"id": "Topic_A"},
            "Topic B": {"id": "Topic_B"},
            "Topic C": {"id": "Topic_C"}
        }
        self.create_discussion("Chapter 1", "Discussion 1")
        self.create_discussion("Chapter 2", "Discussion")
        self.create_discussion("Chapter 2 / Section 1 / Subsection 1", "Discussion")
        self.assertItemsEqual(
            utils.get_discussion_categories_ids(self.course, self.user),
            ["Topic_A", "Topic_B", "Topic_C", "discussion1", "discussion2", "discussion3"]
        )


@attr('shard_1')
class ContentGroupCategoryMapTestCase(CategoryMapTestMixin, ContentGroupTestCase):
    """
    Tests `get_discussion_category_map` on discussion xblocks which are
    only visible to some content groups.
    """
    def test_staff_user(self):
        """
        Verify that the staff user can access the alpha, beta, and
        global discussion topics.
        """
        self.assert_category_map_equals(
            {
                'subcategories': {
                    'Week 1': {
                        'subcategories': {},
                        'children': [
                            'Visible to Alpha',
                            'Visible to Beta',
                            'Visible to Everyone'
                        ],
                        'entries': {
                            'Visible to Alpha': {
                                'sort_key': None,
                                'is_cohorted': True,
                                'id': 'alpha_group_discussion'
                            },
                            'Visible to Beta': {
                                'sort_key': None,
                                'is_cohorted': True,
                                'id': 'beta_group_discussion'
                            },
                            'Visible to Everyone': {
                                'sort_key': None,
                                'is_cohorted': True,
                                'id': 'global_group_discussion'
                            }
                        }
                    }
                },
                'children': ['General', 'Week 1'],
                'entries': {
                    'General': {
                        'sort_key': 'General',
                        'is_cohorted': False,
                        'id': 'i4x-org-number-course-run'
                    }
                }
            },
            requesting_user=self.staff_user
        )

    def test_alpha_user(self):
        """
        Verify that the alpha user can access the alpha and global
        discussion topics.
        """
        self.assert_category_map_equals(
            {
                'subcategories': {
                    'Week 1': {
                        'subcategories': {},
                        'children': [
                            'Visible to Alpha',
                            'Visible to Everyone'
                        ],
                        'entries': {
                            'Visible to Alpha': {
                                'sort_key': None,
                                'is_cohorted': True,
                                'id': 'alpha_group_discussion'
                            },
                            'Visible to Everyone': {
                                'sort_key': None,
                                'is_cohorted': True,
                                'id': 'global_group_discussion'
                            }
                        }
                    }
                },
                'children': ['General', 'Week 1'],
                'entries': {
                    'General': {
                        'sort_key': 'General',
                        'is_cohorted': False,
                        'id': 'i4x-org-number-course-run'
                    }
                }
            },
            requesting_user=self.alpha_user
        )

    def test_beta_user(self):
        """
        Verify that the beta user can access the beta and global
        discussion topics.
        """
        self.assert_category_map_equals(
            {
                'subcategories': {
                    'Week 1': {
                        'subcategories': {},
                        'children': [
                            'Visible to Beta',
                            'Visible to Everyone'
                        ],
                        'entries': {
                            'Visible to Beta': {
                                'sort_key': None,
                                'is_cohorted': True,
                                'id': 'beta_group_discussion'
                            },
                            'Visible to Everyone': {
                                'sort_key': None,
                                'is_cohorted': True,
                                'id': 'global_group_discussion'
                            }
                        }
                    }
                },
                'children': ['General', 'Week 1'],
                'entries': {
                    'General': {
                        'sort_key': 'General',
                        'is_cohorted': False,
                        'id': 'i4x-org-number-course-run'
                    }
                }
            },
            requesting_user=self.beta_user
        )

    def test_non_cohorted_user(self):
        """
        Verify that the non-cohorted user can access the global
        discussion topic.
        """
        self.assert_category_map_equals(
            {
                'subcategories': {
                    'Week 1': {
                        'subcategories': {},
                        'children': [
                            'Visible to Everyone'
                        ],
                        'entries': {
                            'Visible to Everyone': {
                                'sort_key': None,
                                'is_cohorted': True,
                                'id': 'global_group_discussion'
                            }
                        }
                    }
                },
                'children': ['General', 'Week 1'],
                'entries': {
                    'General': {
                        'sort_key': 'General',
                        'is_cohorted': False,
                        'id': 'i4x-org-number-course-run'
                    }
                }
            },
            requesting_user=self.non_cohorted_user
        )


class JsonResponseTestCase(TestCase, UnicodeTestMixin):
    def _test_unicode_data(self, text):
        response = utils.JsonResponse(text)
        reparsed = json.loads(response.content)
        self.assertEqual(reparsed, text)


@attr('shard_1')
class RenderMustacheTests(TestCase):
    """
    Test the `render_mustache` utility function.
    """

    @mock.patch('edxmako.LOOKUP', {})
    def test_it(self):
        """
        Basic test.
        """
        add_lookup('main', '', package=__name__)
        self.assertEqual(utils.render_mustache('test.mustache', {}), 'Testing 1 2 3.\n')


class DiscussionTabTestCase(ModuleStoreTestCase):
    """ Test visibility of the discussion tab. """

    def setUp(self):
        super(DiscussionTabTestCase, self).setUp()
        self.course = CourseFactory.create()
        self.enrolled_user = UserFactory.create()
        self.staff_user = AdminFactory.create()
        CourseEnrollmentFactory.create(user=self.enrolled_user, course_id=self.course.id)
        self.unenrolled_user = UserFactory.create()

    def discussion_tab_present(self, user):
        """ Returns true if the user has access to the discussion tab. """
        request = RequestFactory().request()
        request.user = user
        all_tabs = get_course_tab_list(request, self.course)
        return any(tab.type == 'discussion' for tab in all_tabs)

    def test_tab_access(self):
        with self.settings(FEATURES={'ENABLE_DISCUSSION_SERVICE': True}):
            self.assertTrue(self.discussion_tab_present(self.staff_user))
            self.assertTrue(self.discussion_tab_present(self.enrolled_user))
            self.assertFalse(self.discussion_tab_present(self.unenrolled_user))

    @mock.patch('ccx.overrides.get_current_ccx')
    def test_tab_settings(self, mock_get_ccx):
        mock_get_ccx.return_value = True
        with self.settings(FEATURES={'ENABLE_DISCUSSION_SERVICE': False}):
            self.assertFalse(self.discussion_tab_present(self.enrolled_user))

        with self.settings(FEATURES={'CUSTOM_COURSES_EDX': True}):
            self.assertFalse(self.discussion_tab_present(self.enrolled_user))


class IsCommentableCohortedTestCase(ModuleStoreTestCase):
    """
    Test the is_commentable_cohorted function.
    """

    MODULESTORE = TEST_DATA_MIXED_MODULESTORE

    def setUp(self):
        """
        Make sure that course is reloaded every time--clear out the modulestore.
        """
        super(IsCommentableCohortedTestCase, self).setUp()
        self.toy_course_key = ToyCourseFactory.create().id

    def test_is_commentable_cohorted(self):
        course = modulestore().get_course(self.toy_course_key)
        self.assertFalse(cohorts.is_course_cohorted(course.id))

        def to_id(name):
            """Helper for topic_name_to_id that uses course."""
            return topic_name_to_id(course, name)

        # no topics
        self.assertFalse(
            utils.is_commentable_cohorted(course.id, to_id("General")),
            "Course doesn't even have a 'General' topic"
        )

        # not cohorted
        config_course_cohorts(course, is_cohorted=False, discussion_topics=["General", "Feedback"])

        self.assertFalse(
            utils.is_commentable_cohorted(course.id, to_id("General")),
            "Course isn't cohorted"
        )

        # cohorted, but top level topics aren't
        config_course_cohorts(course, is_cohorted=True, discussion_topics=["General", "Feedback"])

        self.assertTrue(cohorts.is_course_cohorted(course.id))
        self.assertFalse(
            utils.is_commentable_cohorted(course.id, to_id("General")),
            "Course is cohorted, but 'General' isn't."
        )

        # cohorted, including "Feedback" top-level topics aren't
        config_course_cohorts(
            course,
            is_cohorted=True,
            discussion_topics=["General", "Feedback"],
            cohorted_discussions=["Feedback"]
        )

        self.assertTrue(cohorts.is_course_cohorted(course.id))
        self.assertFalse(
            utils.is_commentable_cohorted(course.id, to_id("General")),
            "Course is cohorted, but 'General' isn't."
        )
        self.assertTrue(
            utils.is_commentable_cohorted(course.id, to_id("Feedback")),
            "Feedback was listed as cohorted.  Should be."
        )

    def test_is_commentable_cohorted_inline_discussion(self):
        course = modulestore().get_course(self.toy_course_key)
        self.assertFalse(cohorts.is_course_cohorted(course.id))

        def to_id(name):  # pylint: disable=missing-docstring
            return topic_name_to_id(course, name)

        config_course_cohorts(
            course,
            is_cohorted=True,
            discussion_topics=["General", "Feedback"],
            cohorted_discussions=["Feedback", "random_inline"]
        )
        self.assertTrue(
            utils.is_commentable_cohorted(course.id, to_id("random")),
            "By default, Non-top-level discussion is always cohorted in cohorted courses."
        )

        # if always_cohort_inline_discussions is set to False, non-top-level discussion are always
        # non cohorted unless they are explicitly set in cohorted_discussions
        config_course_cohorts(
            course,
            is_cohorted=True,
            discussion_topics=["General", "Feedback"],
            cohorted_discussions=["Feedback", "random_inline"],
            always_cohort_inline_discussions=False
        )
        self.assertFalse(
            utils.is_commentable_cohorted(course.id, to_id("random")),
            "Non-top-level discussion is not cohorted if always_cohort_inline_discussions is False."
        )
        self.assertTrue(
            utils.is_commentable_cohorted(course.id, to_id("random_inline")),
            "If always_cohort_inline_discussions set to False, Non-top-level discussion is "
            "cohorted if explicitly set in cohorted_discussions."
        )
        self.assertTrue(
            utils.is_commentable_cohorted(course.id, to_id("Feedback")),
            "If always_cohort_inline_discussions set to False, top-level discussion are not affected."
        )

    def test_is_commentable_cohorted_team(self):
        course = modulestore().get_course(self.toy_course_key)
        self.assertFalse(cohorts.is_course_cohorted(course.id))

        config_course_cohorts(course, is_cohorted=True)
        team = CourseTeamFactory(course_id=course.id)

        # Verify that team discussions are not cohorted, but other discussions are
        self.assertFalse(utils.is_commentable_cohorted(course.id, team.discussion_topic_id))
        self.assertTrue(utils.is_commentable_cohorted(course.id, "random"))


class PermissionsTestCase(ModuleStoreTestCase):
    """Test utils functionality related to forums "abilities" (permissions)"""

    def test_get_ability(self):
        content = {}
        content['user_id'] = '1'
        content['type'] = 'thread'

        user = mock.Mock()
        user.id = 1

        with mock.patch('django_comment_client.utils.check_permissions_by_view') as check_perm:
            check_perm.return_value = True
            self.assertEqual(utils.get_ability(None, content, user), {
                'editable': True,
                'can_reply': True,
                'can_delete': True,
                'can_openclose': True,
                'can_vote': False,
                'can_report': False
            })

            content['user_id'] = '2'
            self.assertEqual(utils.get_ability(None, content, user), {
                'editable': True,
                'can_reply': True,
                'can_delete': True,
                'can_openclose': True,
                'can_vote': True,
                'can_report': True
            })

    def test_is_content_authored_by(self):
        content = {}
        user = mock.Mock()
        user.id = 1

        # strict equality checking
        content['user_id'] = 1
        self.assertTrue(utils.is_content_authored_by(content, user))

        # cast from string to int
        content['user_id'] = '1'
        self.assertTrue(utils.is_content_authored_by(content, user))

        # strict equality checking, fails
        content['user_id'] = 2
        self.assertFalse(utils.is_content_authored_by(content, user))

        # cast from string to int, fails
        content['user_id'] = 'string'
        self.assertFalse(utils.is_content_authored_by(content, user))

        # content has no known author
        del content['user_id']
        self.assertFalse(utils.is_content_authored_by(content, user))
