from django.test import TestCase
from django.test.utils import override_settings
from django.conf import settings
from mock import patch
from nose.plugins.skip import SkipTest

import jabber.utils

class JabberSettingsTests(TestCase):
    @override_settings()
    def test_valid_settings(self):
        pass

    def test_missing_settings(self):
        pass


class UtilsTests(TestCase):
    def test_get_bosh_url(self):
        # USE_SSL present (True/False) and absent
        # HOST present (something/empty) and absent
        # PORT present (int/str) and absent
        # PATH present (something/empty) and absent
        pass


    def test_get_password_for_user(self):
        # Test JabberUser present/absent
        pass

    def test_get_room_name_for_course(self):
        # HOST present (something/empty) and absent
        # Test course_id parsing
        pass

