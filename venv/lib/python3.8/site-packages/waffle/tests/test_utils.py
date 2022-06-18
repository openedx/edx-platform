from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings

from waffle import defaults
from waffle.utils import get_setting


class GetSettingTests(TestCase):
    def test_overridden_setting(self):
        prefix = get_setting('CACHE_PREFIX')
        self.assertEqual(settings.WAFFLE_CACHE_PREFIX, prefix)

    def test_default_setting(self):
        age = get_setting('MAX_AGE')
        self.assertEqual(defaults.MAX_AGE, age)

    def test_override_settings(self):
        assert not get_setting('OVERRIDE')
        with override_settings(WAFFLE_OVERRIDE=True):
            assert get_setting('OVERRIDE')
