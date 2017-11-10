"""
All tests regarding scopes.py
"""

from django.test import TestCase
from django.contrib.auth.models import User

from edx_notifications.scopes import (
    SingleUserScopeResolver,
    NotificationUserScopeResolver,
    register_user_scope_resolver,
    clear_user_scope_resolvers,
    resolve_user_scope,
)


class TestListScopeResolver(NotificationUserScopeResolver):
    """
    Test scope resolver that should work
    """

    def resolve(self, scope_name, scope_context, instance_context):
        """
        Resolves the scopes
        """

        if scope_name == 'list_scope':
            return [num for num in range(scope_context['range'])]

        if scope_name == 'badtype_scope':
            return 1

        return None


class TestGeneratorScopeResolver(NotificationUserScopeResolver):
    """
    Test scope resolver that should work
    """

    def resolve(self, scope_name, scope_context, instance_context):
        """
        Resolves the scopes
        """

        if scope_name == 'generator_scope':
            def _scope_generator():
                """
                To test handling of generator
                """
                for user_id in range(scope_context['range']):
                    yield user_id

            return _scope_generator()

        return None


class DjangoORMResolver(NotificationUserScopeResolver):
    """
    Test scope resolver that returns a database query
    """

    def resolve(self, scope_name, scope_context, instance_context):
        """
        Handles both the ValuesListQuerySet and the ValuesQuerySet
        """

        if scope_name == 'values_list_query_set':
            return User.objects.values_list('id', flat=True).all()  # pylint: disable=no-member
        elif scope_name == 'values_query_set':
            return User.objects.values('id').all()  # pylint: disable=no-member


class BadTestScopeResolver(NotificationUserScopeResolver):
    """
    Test scope resolver that should not work
    """

    def resolve(self, scope_name, scope_context, instance_context):
        """
        Should fail
        """
        super(BadTestScopeResolver, self).resolve(scope_name, scope_context, instance_context)


class ScopesTests(TestCase):
    """
    Provide tests of scopes.py
    """

    def setUp(self):
        clear_user_scope_resolvers()
        register_user_scope_resolver('list_scope', TestListScopeResolver())
        register_user_scope_resolver('generator_scope', TestGeneratorScopeResolver())
        register_user_scope_resolver('values_list_query_set', DjangoORMResolver())
        register_user_scope_resolver('values_query_set', DjangoORMResolver())

        # create a test user in the Django ORM

        self.test_user = User(username='foo', email='foo@bar.com', first_name='Foo', last_name='Bar')
        self.test_user.is_active = True
        self.test_user.save()

    def test_resolving_scope(self):
        """
        Happy path scope resolving
        """

        user_ids = resolve_user_scope('list_scope', {'range': 5})

        self.assertIsNotNone(user_ids)
        self.assertEqual(len(user_ids), 5)
        self.assertEqual(user_ids, [num for num in range(5)])

        user_ids = resolve_user_scope('generator_scope', {'range': 10})

        self.assertIsNotNone(user_ids)
        compare = []
        for user_id in user_ids:
            compare.append(user_id)

        # generators dont support len()
        self.assertEqual(compare, [num for num in range(10)])

    def test_no_resolve(self):
        """
        Asserts that None is returned when there is scope resolution
        """

        with self.assertRaises(TypeError):
            resolve_user_scope('bad_scope', {})

    def test_no_instantiation(self):
        """
        Asserts that NotificationScopeResolver is an abstract base clas
        """

        with self.assertRaises(TypeError):
            NotificationUserScopeResolver()

        register_user_scope_resolver('bad_scope', BadTestScopeResolver())

        with self.assertRaises(NotImplementedError):
            resolve_user_scope('bad_scope', {})

    def test_bad_return_type(self):
        """
        Asserts that we can't allow for an illegal type to
        be returned
        """

        register_user_scope_resolver('badtype_scope', TestListScopeResolver())

        with self.assertRaises(TypeError):
            resolve_user_scope('badtype_scope', {})

    def test_no_resolver(self):
        """
        Asserts that an exception is raised when we try to resolve
        via a non-existing scope_name
        """

        with self.assertRaises(TypeError):
            resolve_user_scope('non-existing', {})

    def test_no_resolution(self):
        """
        Asserts that None is returned if the Resolvers can resolve
        """

        register_user_scope_resolver('none_resolver', TestListScopeResolver())

        self.assertIsNone(resolve_user_scope('none_resolver', {}))

    def test_single_user_scope_resolver(self):
        """
        Assert that we can resolve the system defined SingleUserScopeResolver
        """

        resolver = SingleUserScopeResolver()
        user_ids = resolver.resolve('user', {'user_id': 1}, {})
        self.assertEquals(user_ids, [1])

    def test_django_orm_based_resolver(self):
        """
        Assert proper operations when working with Django ORM cursors
        """

        users = resolve_user_scope('values_list_query_set', {})
        users_list = [user for user in users]
        self.assertEqual(len(users_list), 1)
        self.assertEqual(users_list[0], self.test_user.id)

        users = resolve_user_scope('values_query_set', {})
        users_list = [user for user in users]
        self.assertEqual(len(users_list), 1)
        self.assertEqual(users_list[0]['id'], self.test_user.id)
