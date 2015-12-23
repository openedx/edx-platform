"""
Some additional unit tests for Microsite logic. The LMS covers some of the Microsite testing, this adds
some additional coverage
"""
import ddt
from mock import patch

from microsite_configuration.microsite import (
    get_value_for_org,
    get_backend,
)
from microsite_configuration.backends.base import BaseMicrositeBackend
from microsite_configuration.tests.tests import (
    MicrositeTest,
    MICROSITE_BACKENDS,
)


@ddt.ddt
class TestMicrosites(MicrositeTest):
    """
    Run through some Microsite logic
    """

    def setUp(self):
        super(TestMicrosites, self).setUp()

    @ddt.data(*MICROSITE_BACKENDS)
    def test_get_value_for_org(self, site_backend):
        """
        Make sure we can do lookups on Microsite configuration based on ORG fields
        """

        with patch('microsite_configuration.microsite.BACKEND', get_backend(site_backend, BaseMicrositeBackend)):
            # first make sure default value is returned if there's no Microsite ORG match
            value = get_value_for_org("BogusX", "university", "default_value")
            self.assertEquals(value, "default_value")

            # now test when we call in a value Microsite ORG, note this is defined in test.py configuration
            value = get_value_for_org("TestMicrositeX", "university", "default_value")
            self.assertEquals(value, "test_microsite")
