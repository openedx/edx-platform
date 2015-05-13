"""
Test for student tasks.
"""

from student.tests.factories import UserFactory, CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from student.models import CourseEnrollment
from student.scope_resolver import (
    CourseEnrollmentsScopeResolver,
    StudentEmailScopeResolver,
    NamespaceEnrollmentsScopeResolver
)


class StudentTasksTestCase(ModuleStoreTestCase):
    """
    Tests of student.roles
    """

    def setUp(self):
        """
        setUp stuff
        """
        super(StudentTasksTestCase, self).setUp()
        self.course = CourseFactory.create()

    def test_resolve_course_enrollments(self):
        """
        Test that the CourseEnrollmentsScopeResolver actually returns all enrollments
        """

        test_user_1 = UserFactory.create(password='test_pass')
        CourseEnrollmentFactory(user=test_user_1, course_id=self.course.id)
        test_user_2 = UserFactory.create(password='test_pass')
        CourseEnrollmentFactory(user=test_user_2, course_id=self.course.id)
        test_user_3 = UserFactory.create(password='test_pass')
        enrollment = CourseEnrollmentFactory(user=test_user_3, course_id=self.course.id)

        # unenroll #3

        enrollment.is_active = False
        enrollment.save()

        resolver = CourseEnrollmentsScopeResolver()

        user_ids = resolver.resolve('course_enrollments', {'course_id': self.course.id}, None)

        # should have first two, but the third should not be present

        self.assertTrue(test_user_1.id in user_ids)
        self.assertTrue(test_user_2.id in user_ids)

        self.assertFalse(test_user_3.id in user_ids)

    def test_bad_params(self):
        """
        Makes sure the resolver returns None if all parameters aren't passed
        """

        resolver = CourseEnrollmentsScopeResolver()

        self.assertIsNone(resolver.resolve('bad', {'course_id': 'foo'}, None))

        with self.assertRaises(KeyError):
            self.assertIsNone(resolver.resolve('course_enrollments', {'bad': 'foo'}, None))

    def test_namespace_scope(self):
        """
        Make sure that we handle resolving namespaces correctly
        """

        test_user_1 = UserFactory.create(
            password='test_pass',
            email='user1@foo.com',
            first_name='user',
            last_name='one'
        )
        CourseEnrollmentFactory(user=test_user_1, course_id=self.course.id)

        test_user_2 = UserFactory.create(
            password='test_pass',
            email='user2@foo.com',
            first_name='John',
            last_name='Smith'
        )
        CourseEnrollmentFactory(user=test_user_2, course_id=self.course.id)

        test_user_3 = UserFactory.create(password='test_pass')
        enrollment = CourseEnrollmentFactory(user=test_user_3, course_id=self.course.id)

        # unenroll #3

        enrollment.is_active = False
        enrollment.save()

        resolver = NamespaceEnrollmentsScopeResolver()

        users = resolver.resolve(
            'namespace_scope',
            {
                'namespace': self.course.id,
                'fields': {
                    'id': True,
                    'email': True,
                    'first_name': True,
                    'last_name': True,
                }
            },
            None
        )

        _users = [user for user in users]

        self.assertEqual(len(_users), 2)

        self.assertIn('id', _users[0])
        self.assertIn('email', _users[0])
        self.assertIn('first_name', _users[0])
        self.assertIn('last_name', _users[0])
        self.assertEquals(_users[0]['id'], test_user_1.id)
        self.assertEquals(_users[0]['email'], test_user_1.email)
        self.assertEquals(_users[0]['first_name'], test_user_1.first_name)
        self.assertEquals(_users[0]['last_name'], test_user_1.last_name)

        self.assertIn('id', _users[1])
        self.assertIn('email', _users[1])
        self.assertIn('first_name', _users[1])
        self.assertIn('last_name', _users[1])
        self.assertEquals(_users[1]['id'], test_user_2.id)
        self.assertEquals(_users[1]['email'], test_user_2.email)
        self.assertEquals(_users[1]['first_name'], test_user_2.first_name)
        self.assertEquals(_users[1]['last_name'], test_user_2.last_name)

    def test_email_resolver(self):
        """
        Make sure we can resolve emails
        """
        test_user_1 = UserFactory.create(password='test_pass')

        resolver = StudentEmailScopeResolver()

        resolved_scopes = resolver.resolve(
            'user_email_resolver',
            {
                'user_id': test_user_1.id,
            },
            None
        )

        emails = [resolved_scope['email'] for resolved_scope in resolved_scopes]

        self.assertTrue(test_user_1.email in emails)

    def test_bad_email_resolver(self):
        """
        Cover some error cases
        """
        resolver = StudentEmailScopeResolver()
        self.assertIsNone(resolver.resolve('bad', {'course_id': 'foo'}, None))
        self.assertIsNone(resolver.resolve('course_enrollments', {'bad': 'foo'}, None))
