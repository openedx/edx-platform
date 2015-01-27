# -*- coding: utf-8 -*-
from datetime import datetime
import json
from pytz import UTC

from django.core.urlresolvers import reverse
from django.test import TestCase
from edxmako import add_lookup
import mock

from django_comment_client.tests.factories import RoleFactory
from django_comment_client.tests.unicode import UnicodeTestMixin
from django_comment_client.tests.utils import ContentGroupTestCase
import django_comment_client.utils as utils
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


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


class AccessUtilsTestCase(ModuleStoreTestCase):
    """
    Base testcase class for access and roles for the
    comment client service integration
    """
    def setUp(self):
        super(AccessUtilsTestCase, self).setUp(create_user=False)

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

    def test_get_role_ids(self):
        ret = utils.get_role_ids(self.course_id)
        expected = {u'Moderator': [3], u'Community TA': [4, 5]}
        self.assertEqual(ret, expected)

    def test_has_forum_access(self):
        ret = utils.has_forum_access('student', self.course_id, 'Student')
        self.assertTrue(ret)

        ret = utils.has_forum_access('not_a_student', self.course_id, 'Student')
        self.assertFalse(ret)

        ret = utils.has_forum_access('student', self.course_id, 'NotARole')
        self.assertFalse(ret)


class CoursewareContextTestCase(ModuleStoreTestCase):
    """
    Base testcase class for courseware context for the
    comment client service integration
    """
    def setUp(self):
        super(CoursewareContextTestCase, self).setUp(create_user=True)

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


class CategoryMapTestCase(CategoryMapTestMixin, ModuleStoreTestCase):
    """
    Base testcase class for discussion categories for the
    comment client service integration
    """
    def setUp(self):
        super(CategoryMapTestCase, self).setUp(create_user=True)

        self.course = CourseFactory.create(
            org="TestX", number="101", display_name="Test Course",
            # This test needs to use a course that has already started --
            # discussion topics only show up if the course has already started,
            # and the default start date for courses is Jan 1, 2030.
            start=datetime(2012, 2, 3, tzinfo=UTC)
        )
        # Courses get a default discussion topic on creation, so remove it
        self.course.discussion_topics = {}
        self.course.save()
        self.discussion_num = 0
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

    def test_empty(self):
        self.assert_category_map_equals({"entries": {}, "subcategories": {}, "children": []})

    def test_configured_topics(self):
        self.course.discussion_topics = {
            "Topic A": {"id": "Topic_A"},
            "Topic B": {"id": "Topic_B"},
            "Topic C": {"id": "Topic_C"}
        }

        def check_cohorted_topics(expected_ids):
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

        self.course.cohort_config = {"cohorted": False, "cohorted_discussions": []}
        check_cohorted_topics([])

        self.course.cohort_config = {"cohorted": True, "cohorted_discussions": []}
        check_cohorted_topics([])

        self.course.cohort_config = {"cohorted": True, "cohorted_discussions": ["Topic_B", "Topic_C"]}
        check_cohorted_topics(["Topic_B", "Topic_C"])

        self.course.cohort_config = {"cohorted": True, "cohorted_discussions": ["Topic_A", "Some_Other_Topic"]}
        check_cohorted_topics(["Topic_A"])

        # unlikely case, but make sure it works.
        self.course.cohort_config = {"cohorted": False, "cohorted_discussions": ["Topic_A"]}
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
        self.course.cohort_config = {"cohorted": False}
        check_cohorted(False)

        # explicitly enabled cohorting
        self.course.cohort_config = {"cohorted": True}
        check_cohorted(True)

    def test_start_date_filter(self):
        now = datetime.now()
        later = datetime.max
        self.create_discussion("Chapter 1", "Discussion 1", start=now)
        self.create_discussion("Chapter 1", "Discussion 2 обсуждение", start=later)
        self.create_discussion("Chapter 2", "Discussion", start=now)
        self.create_discussion("Chapter 2 / Section 1 / Subsection 1", "Discussion", start=later)
        self.create_discussion("Chapter 2 / Section 1 / Subsection 2", "Discussion", start=later)
        self.create_discussion("Chapter 3 / Section 1", "Discussion", start=later)

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


class ContentGroupCategoryMapTestCase(CategoryMapTestMixin, ContentGroupTestCase):
    """
    Tests `get_discussion_category_map` on discussion modules which are
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
