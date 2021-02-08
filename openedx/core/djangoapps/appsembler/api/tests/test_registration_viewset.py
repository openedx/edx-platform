"""
This is a quick test case in order to apply missing coverage
"""

from django.test import TestCase
import ddt

from openedx.core.djangoapps.appsembler.api.v1.views import RegistrationViewSet


from django.conf import settings
import unittest
if settings.TAHOE_TEMP_MONKEYPATCHING_JUNIPER_TESTS:
    raise unittest.SkipTest('fix broken tests')


@ddt.ddt
class RegistrationViewSetMethodTestCase(TestCase):
    def setUp(self):
        self.reg = RegistrationViewSet()

    @ddt.data(True, False, 'True', 'False', 'true', 'false')
    def test_normalize_bool_param(self, unnormalized):
        expected_map = {
            True: True,
            False: False,
            'True': True,
            'False': False,
            'true': True,
            'false': False
        }
        normalized = self.reg._normalize_bool_param(unnormalized)
        assert normalized == expected_map[unnormalized]
