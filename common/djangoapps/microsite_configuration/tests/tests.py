"""
Holds base classes for microsite tests
"""
from mock import DEFAULT

from django.test import TestCase
from microsite_configuration.tests.factories import (
    MicrositeFactory,
    MicrositeOrgMappingFactory,
)

MICROSITE_BACKENDS = (
    'microsite_configuration.backends.filebased.SettingsFileMicrositeBackend',
    'microsite_configuration.backends.database.DatabaseMicrositeBackend',
)


class MicrositeTest(TestCase):

    def setUp(self):
        super(MicrositeTest, self).setUp()
        microsite = MicrositeFactory.create()
        MicrositeOrgMappingFactory.create(microsite=microsite, org='TestMicrositeX')


def side_effect_for_get_value(value, return_value):
    """
    returns a side_effect with given return value for a given value
    """
    def side_effect(*args, **kwargs):
        if args[0] == value:
            return return_value
        else:
            return DEFAULT
    return side_effect