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
    DatabaseMicrositeTestCase,
    MICROSITE_BACKENDS,
)


@ddt.ddt
class TestMicrosites(DatabaseMicrositeTestCase):
    """
    Run through some Microsite logic
    """

    def setUp(self):
        super(TestMicrosites, self).setUp()

    @ddt.data(*MICROSITE_BACKENDS)
    def test_get_value_for_org_when_microsite_has_no_org(self, site_backend):
        """
        Make sure default value is returned if there's no Microsite ORG match
        """
        with patch('microsite_configuration.microsite.BACKEND',
                   get_backend(site_backend, BaseMicrositeBackend)):
            value = get_value_for_org("BogusX", "university", "default_value")
            self.assertEquals(value, "default_value")

    @ddt.data(*MICROSITE_BACKENDS)
    def test_get_value_for_org(self, site_backend):
        """
        Make sure get_value_for_org return value of org if it present.
        """
        with patch('microsite_configuration.microsite.BACKEND',
                   get_backend(site_backend, BaseMicrositeBackend)):
            value = get_value_for_org("TestSiteX", "university", "default_value")
            self.assertEquals(value, "test_site")
