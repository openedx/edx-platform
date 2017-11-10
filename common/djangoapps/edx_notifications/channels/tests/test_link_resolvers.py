"""
Unit tests for the resolvers.py file
"""

from django.test import TestCase

from edx_notifications.channels.link_resolvers import (
    BaseLinkResolver,
    MsgTypeToUrlLinkResolver,
)


class BadLinkResolver(BaseLinkResolver):
    """
    A test link resolver which should throw exceptions because
    it does not do what it is supposed to do per
    the abstract interface contract
    """

    def resolve(self, msg_type_name, link_name, params, exact_match_only=False):
        """
        Simply call into our parent which show throw exception
        """
        return super(BadLinkResolver, self).resolve(msg_type_name, link_name, params, exact_match_only=exact_match_only)


class BaseLinkResolverTests(TestCase):
    """
    Assert that the abstract interface is right
    """

    def test_create_abstract_class(self):
        """
        Asserts that we cannot create an instance of the
        abstract class
        """
        with self.assertRaises(TypeError):
            BaseLinkResolver()  # pylint: disable=abstract-class-instantiated

    def test_throws_exception(self):
        """
        Confirms that the base abstract class will raise an exception
        """

        with self.assertRaises(NotImplementedError):
            BadLinkResolver().resolve(None, None, None)


class MsgTypeToUrlLinkResolverTests(TestCase):
    """
    Make sure things resolve as we expect them to
    """

    def setUp(self):
        """
        Setup stuff
        """

        self.resolver_maps_config = {
            '_click_link': {
                # this will conver msg type 'test-type.type-with-links'
                # to /path/to/{param1}/url/{param2} with param subsitutations
                # that are passed in with the message
                'test-type.type-with-links': '/path/to/{param1}/url/{param2}',
                'test-type.*': '/parent/{param1}',
                '*': '/root',
            }
        }

    def test_resolve(self):
        """
        Assert we can resolve a well formed type_name, link_name, and params
        """

        resolver = MsgTypeToUrlLinkResolver(self.resolver_maps_config)

        resolve_params = {
            'param1': 'foo',
            'param2': 'bar',
        }

        url = resolver.resolve(
            'test-type.type-with-links',
            '_click_link',
            resolve_params
        )
        self.assertEqual(url, '/path/to/foo/url/bar')

        # now see if first wildcard properly resolves
        url = resolver.resolve(
            'test-type.different',
            '_click_link',
            resolve_params
        )
        self.assertEqual(url, '/parent/foo')

        # now see if the global wildcard resolves
        url = resolver.resolve(
            'only-match-at-root',
            '_click_link',
            resolve_params
        )
        self.assertEqual(url, '/root')

    def test_missing_type(self):
        """
        Failure case when the msg_type cannot be found
        """

        resolver = MsgTypeToUrlLinkResolver({
            '_click_link': {
                # this will conver msg type 'test-type.type-with-links'
                # to /path/to/{param1}/url/{param2} with param subsitutations
                # that are passed in with the message
                'test-type.type-with-links': '/path/to/{param1}/url/{param2}'
            }
        })

        url = resolver.resolve(
            'test-type.missing-type',
            '_click_link',
            {
                'param1': 'foo',
                'param2': 'bar',
            }
        )
        self.assertIsNone(url)

    def test_missing_link_name(self):
        """
        Failure case when the link_name cannot be found
        """

        resolver = MsgTypeToUrlLinkResolver({
            '_click_link': {
                # this will conver msg type 'test-type.type-with-links'
                # to /path/to/{param1}/url/{param2} with param subsitutations
                # that are passed in with the message
                'test-type.type-with-links': '/path/to/{param1}/url/{param2}'
            }
        })

        url = resolver.resolve(
            'test-type.type-with-links',
            'missing_link_name',
            {
                'param1': 'foo',
                'param2': 'bar',
            }
        )
        self.assertIsNone(url)

    def test_missing_formatting_param(self):
        """
        Failure case wheen the msg_type cannot be found
        """

        resolver = MsgTypeToUrlLinkResolver({
            '_click_link': {
                # this will conver msg type 'test-type.type-with-links'
                # to /path/to/{param1}/url/{param2} with param subsitutations
                # that are passed in with the message
                'test-type.type-with-links': '/path/to/{param1}/url/{param2}'
            }
        })

        url = resolver.resolve(
            'test-type.type-with-links',
            '_click_link',
            {
                'param1': 'foo',
            }
        )
        self.assertIsNone(url)
