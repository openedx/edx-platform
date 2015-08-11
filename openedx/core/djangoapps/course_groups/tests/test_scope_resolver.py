"""
Test cases for scope_resolver.py
"""

from django.test import TestCase
from student.tests.factories import UserFactory

from ..scope_resolver import CourseGroupScopeResolver
from .test_views import CohortFactory


class ScopeResolverTests(TestCase):
    """
    Tests for the scope resolver
    """

    def setUp(self):
        """Creates cohorts for testing"""
        super(ScopeResolverTests, self).setUp()
        self.course_id = 'foo/bar/baz'
        self.cohort1_users = [UserFactory.create() for _ in range(3)]
        self.cohort2_users = [UserFactory.create() for _ in range(2)]
        self.cohort3_users = [UserFactory.create() for _ in range(2)]

        self.cohort1 = CohortFactory.create(course_id=self.course_id, users=self.cohort1_users)
        self.cohort2 = CohortFactory.create(course_id=self.course_id, users=self.cohort2_users)
        self.cohort3 = CohortFactory.create(course_id=self.course_id, users=self.cohort3_users)

    def test_resolve_cohort(self):
        """
        Given the defined cohorts in the setUp, make sure the
        """

        resolver = CourseGroupScopeResolver()

        user_ids = resolver.resolve('course_group', {'group_id': self.cohort1.id}, None).all()

        self.assertEqual(
            [user_id for user_id in user_ids],
            [user.id for user in self.cohort1_users]
        )

    def test_bad_params(self):
        """
        Given the defined cohorts in the setUp, make sure the
        """

        resolver = CourseGroupScopeResolver()

        self.assertIsNone(resolver.resolve('bad', {'group_id': self.cohort1.id}, None))

        self.assertIsNone(resolver.resolve('course_group', {'bad': self.cohort1.id}, None))
