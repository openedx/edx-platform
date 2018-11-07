# pylint: disable=missing-docstring
from urlparse import parse_qs, urlparse


class QueryStringAssertionMixin(object):

    def assert_query_string_equal(self, expected_qs, actual_qs):
        """
        Compares two query strings to see if they are equivalent. Note that order of parameters is not significant.

        Args:
            expected_qs (str): The expected query string.
            actual_qs (str): The actual query string.

        Raises:
            AssertionError: If the two query strings are not equal.
        """
        self.assertDictEqual(parse_qs(expected_qs), parse_qs(actual_qs))

    def assert_url_components_equal(self, url, **kwargs):
        """
        Assert that the provided URL has the expected components with the expected values.

        Args:
            url (str): The URL to parse and make assertions about.
            **kwargs: The expected component values. For example: scheme='https' would assert that the URL scheme was
                https.

        Raises:
            AssertionError: If any of the expected components do not match.
        """
        parsed_url = urlparse(url)
        for expected_component, expected_value in kwargs.items():
            if expected_component == 'query':
                self.assert_query_string_equal(expected_value, parsed_url.query)
            else:
                self.assertEqual(expected_value, getattr(parsed_url, expected_component))

    def assert_query_string_parameters_equal(self, url, **kwargs):
        """
        Assert that the provided URL has query string paramters that match the kwargs.

        Args:
            url (str): The URL to parse and make assertions about.
            **kwargs: The expected query string parameter values. For example: foo='bar' would assert that foo=bar
                appeared in the query string.

        Raises:
            AssertionError: If any of the expected parameters values do not match.
        """
        parsed_url = urlparse(url)
        parsed_qs = parse_qs(parsed_url.query)
        for expected_key, expected_value in kwargs.items():
            self.assertEqual(parsed_qs[expected_key], [str(expected_value)])
