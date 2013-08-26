from django.test import TestCase
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from django_comment_common.models import Role, Permission
from factories import RoleFactory
import django_comment_client.utils as utils


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


class CategorySortTestCase(TestCase):
    def setUp(self):
        self.category_map = {
            'entries': {
                u'General': {
                    'sort_key': u'General'
                }
            },
            'subcategories': {
                u'Tests': {
                    'sort_key': u'Tests',
                    'subcategories': {},
                    'entries': {
                        u'Quizzes': {
                            'sort_key': None
                        }, u'All': {
                            'sort_key': None
                        }, u'Final Exam': {
                            'sort_key': None
                        },
                    }
                },
                u'Assignments': {
                    'sort_key': u'Assignments',
                    'subcategories': {},
                    'entries': {
                        u'Homework': {
                            'sort_key': None
                        },
                        u'All': {
                            'sort_key': None
                        },
                    }
                }
            }
        }

    def test_alpha_sort_true(self):
        expected_true = {
            'entries': {
                u'General': {
                    'sort_key': u'General'
                }
            },
            'children': [u'Assignments', u'General', u'Tests'],
            'subcategories': {
                u'Tests': {
                    'sort_key': u'Tests',
                    'subcategories': {},
                    'children': [u'All', u'Final Exam', u'Quizzes'],
                    'entries': {
                        u'All': {
                            'sort_key': 'All'
                        }, u'Final Exam': {
                            'sort_key': 'Final Exam'
                        }, u'Quizzes': {
                            'sort_key': 'Quizzes'
                        }
                    }
                },
                u'Assignments': {
                    'sort_key': u'Assignments',
                    'subcategories': {},
                    'children': [u'All', u'Homework'],
                    'entries': {
                        u'Homework': {
                            'sort_key': 'Homework'
                        },
                        u'All': {
                            'sort_key': 'All'
                        },
                    }
                }
            }
        }
        
        utils.sort_map_entries(self.category_map, True)
        self.assertEqual(self.category_map, expected_true)

    def test_alpha_sort_false(self):
        expected_false = {
            'entries': {
                u'General': {
                    'sort_key': u'General'
                }
            },
            'children': [u'Assignments', u'General', u'Tests'],
            'subcategories': {
                u'Tests': {
                    'sort_key': u'Tests',
                    'subcategories': {},
                    'children': [u'Quizzes', u'All', u'Final Exam'],
                    'entries': {
                        u'Quizzes': {
                            'sort_key': None
                        }, u'All': {
                            'sort_key': None
                        }, u'Final Exam': {
                            'sort_key': None
                        },
                    }
                },
                u'Assignments': {
                    'sort_key': u'Assignments',
                    'subcategories': {},
                    'children': [u'All', u'Homework'],
                    'entries': {
                        u'Homework': {
                            'sort_key': None
                        },
                        u'All': {
                            'sort_key': None
                        },
                    }
                }
            }
        }
        
        utils.sort_map_entries(self.category_map, False)
        self.assertEqual(self.category_map, expected_false)


class AccessUtilsTestCase(TestCase):
    def setUp(self):
        self.course_id = 'edX/toy/2012_Fall'
        self.student_role = RoleFactory(name='Student', course_id=self.course_id)
        self.moderator_role = RoleFactory(name='Moderator', course_id=self.course_id)
        self.student1 = UserFactory(username='student', email='student@edx.org')
        self.student1_enrollment = CourseEnrollmentFactory(user=self.student1)
        self.student_role.users.add(self.student1)
        self.student2 = UserFactory(username='student2', email='student2@edx.org')
        self.student2_enrollment = CourseEnrollmentFactory(user=self.student2)
        self.moderator = UserFactory(username='moderator', email='staff@edx.org', is_staff=True)
        self.moderator_enrollment = CourseEnrollmentFactory(user=self.moderator)
        self.moderator_role.users.add(self.moderator)

    def test_get_role_ids(self):
        ret = utils.get_role_ids(self.course_id)
        expected = {u'Moderator': [3], u'Student': [1, 2], 'Staff': [3]}
        self.assertEqual(ret, expected)

    def test_has_forum_access(self):
        ret = utils.has_forum_access('student', self.course_id, 'Student')
        self.assertTrue(ret)

        ret = utils.has_forum_access('not_a_student', self.course_id, 'Student')
        self.assertFalse(ret)

        ret = utils.has_forum_access('student', self.course_id, 'NotARole')
        self.assertFalse(ret)
