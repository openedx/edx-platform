"""Tests of comprehensive theming."""

from django.conf import settings
from django.test import TestCase

from openedx.core.djangoapps.theming.test_util import with_comp_theme


class TestComprehensiveTheming(TestCase):
    """Test comprehensive theming."""

    @with_comp_theme(settings.REPO_ROOT / 'themes/red-theme')
    def test_red_footer(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "super-ugly")
