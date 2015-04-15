"""
Unit tests for namespace_resolver.py
"""

from django.test import TestCase

from datetime import datetime

from xmodule.modulestore.tests.factories import CourseFactory
from util.namespace_resolver import CourseNamespaceResolver

from student.scope_resolver import NamespaceEnrollmentsScopeResolver


class NamespaceResolverTests(TestCase):
    """
    Tests for the CourseNamespaceResolver
    """

    def setUp(self):
        """
        Test initialization
        """

        self.course = CourseFactory(
            org='foo',
            start=datetime(1980, 1, 1),
            end=datetime(2200, 1, 1)
        )
        self.closed_course = CourseFactory(
            org='bar',
            start=datetime(1975, 1, 1),
            end=datetime(1980, 1, 1)
        )
        self.not_open_course = CourseFactory(
            org='baz',
            start=datetime(2200, 1, 1),
            end=datetime(2222, 1, 1)
        )

    def test_resolve_namespace(self):
        """
        Make sure the interface is properly implemented
        """

        resolver = CourseNamespaceResolver()

        # can't resolve a non existing course
        self.assertIsNone(resolver.resolve('foo', None))

        # happy path
        result = resolver.resolve(self.course.id, None)

        self.assertIsNotNone(result)
        self.assertEqual(result['namespace'], self.course.id)
        self.assertEqual(result['display_name'], self.course.display_name)
        self.assertTrue(isinstance(result['default_user_resolver'], NamespaceEnrollmentsScopeResolver))
        self.assertTrue(result['features']['digests'])

        # course that is closed
        result = resolver.resolve(self.closed_course.id, None)

        self.assertIsNotNone(result)
        self.assertEqual(result['namespace'], self.closed_course.id)
        self.assertEqual(result['display_name'], self.closed_course.display_name)
        self.assertTrue(isinstance(result['default_user_resolver'], NamespaceEnrollmentsScopeResolver))
        self.assertFalse(result['features']['digests'])

        # course that has not opened
        result = resolver.resolve(self.not_open_course.id, None)

        self.assertIsNotNone(result)
        self.assertEqual(result['namespace'], self.not_open_course.id)
        self.assertEqual(result['display_name'], self.not_open_course.display_name)
        self.assertTrue(isinstance(result['default_user_resolver'], NamespaceEnrollmentsScopeResolver))
        self.assertFalse(result['features']['digests'])
