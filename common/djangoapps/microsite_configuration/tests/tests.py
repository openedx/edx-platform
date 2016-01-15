"""
Holds base classes for microsite tests
"""
from mock import DEFAULT

from django.test import TestCase
from microsite_configuration.tests.factories import (
    MicrositeFactory,
    MicrositeOrganizationMappingFactory,
)

MICROSITE_BACKENDS = (
    'microsite_configuration.backends.filebased.FilebasedMicrositeBackend',
    'microsite_configuration.backends.database.DatabaseMicrositeBackend',
)


class DatabaseMicrositeTestCase(TestCase):
    """
    Base class for microsite related tests.
    """
    def setUp(self):
        super(DatabaseMicrositeTestCase, self).setUp()
        self.microsite = MicrositeFactory.create()
        MicrositeOrganizationMappingFactory.create(microsite=self.microsite, organization='TestMicrositeX')


def side_effect_for_get_value(value, return_value):
    """
    returns a side_effect with given return value for a given value
    """
    def side_effect(*args, **kwargs):  # pylint: disable=unused-argument
        """
        A side effect for tests which returns a value based
        on a given argument otherwise return actual function.
        """
        if args[0] == value:
            return return_value
        else:
            return DEFAULT
    return side_effect
