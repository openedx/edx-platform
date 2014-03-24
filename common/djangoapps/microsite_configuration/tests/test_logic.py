"""
Some additional unit tests for Microsite logic. The LMS covers some of the Microsite testing, this adds
some additional coverage
"""
import django.test

from microsite_configuration.microsite import get_value_for_org


class TestMicrosites(django.test.TestCase):
    """
    Run through some Microsite logic
    """

    def test_get_value_for_org(self):
        """
        Make sure we can do lookups on Microsite configuration based on ORG fields
        """

        # first make sure default value is returned if there's no Microsite ORG match
        value = get_value_for_org("BogusX", "university", "default_value")
        self.assertEquals(value, "default_value")

        # now test when we call in a value Microsite ORG, note this is defined in test.py configuration
        value = get_value_for_org("TestMicrositeX", "university", "default_value")
        self.assertEquals(value, "test_microsite")
