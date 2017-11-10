"""
Unit tests for namespaces.py
"""

from django.test import TestCase

from edx_notifications.namespaces import (
    NotificationNamespaceResolver,
    DefaultNotificationNamespaceResolver,
    register_namespace_resolver,
    resolve_namespace
)


class BadNotificationNamespaceResolver(NotificationNamespaceResolver):
    """
    A resolver that does not properly implement the interface
    """

    def resolve(self, namespace, instance_context):
        """
        Bad resolution
        """
        super(BadNotificationNamespaceResolver, self).resolve(namespace, instance_context)


class TestNamespaces(TestCase):
    """
    Test cases for namespace.py
    """

    def test_no_resolver(self):
        """
        Assert that None is returned
        """
        register_namespace_resolver(None)
        self.assertIsNone(resolve_namespace('foo'))

    def test_default_resolver(self):
        """
        Assert that the default works as expected
        """

        register_namespace_resolver(DefaultNotificationNamespaceResolver())

        namespace = 'foo'
        response = resolve_namespace(namespace)

        self.assertIsNotNone(response)
        self.assertEqual(
            response,
            {
                'namespace': namespace,
                'display_name': namespace,
                'features': {
                    'digests': False,
                },
                'default_user_resolver': None
            }
        )

    def test_bad_resolver(self):
        """
        assert that we get exception when trying to use the bad resolver
        """

        register_namespace_resolver(BadNotificationNamespaceResolver())
        with self.assertRaises(NotImplementedError):
            resolve_namespace('foo')
