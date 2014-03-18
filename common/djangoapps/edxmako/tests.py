from django.test import TestCase
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from edxmako import add_lookup, LOOKUP
from edxmako.shortcuts import marketing_link
from mock import patch
from util.testing import UrlResetMixin


class ShortcutsTests(UrlResetMixin, TestCase):
    """
    Test the edxmako shortcuts file
    """
    @override_settings(MKTG_URLS={'ROOT': 'dummy-root', 'ABOUT': '/about-us'})
    @override_settings(MKTG_URL_LINK_MAP={'ABOUT': 'login'})
    def test_marketing_link(self):
        # test marketing site on
        with patch.dict('django.conf.settings.FEATURES', {'ENABLE_MKTG_SITE': True}):
            expected_link = 'dummy-root/about-us'
            link = marketing_link('ABOUT')
            self.assertEquals(link, expected_link)
        # test marketing site off
        with patch.dict('django.conf.settings.FEATURES', {'ENABLE_MKTG_SITE': False}):
            # we are using login because it is common across both cms and lms
            expected_link = reverse('login')
            link = marketing_link('ABOUT')
            self.assertEquals(link, expected_link)


class AddLookupTests(TestCase):
    """
    Test the `add_lookup` function.
    """
    @patch('edxmako.LOOKUP', {})
    def test_with_package(self):
        add_lookup('test', 'management', __name__)
        dirs = LOOKUP['test'].directories
        self.assertEqual(len(dirs), 1)
        self.assertTrue(dirs[0].endswith('management'))
