"""
Tests that verify that the admin view loads.

This is not inside a django app because it is a global property of the system.
"""
import ddt
from django.test import Client, TestCase
from django.urls import reverse
from edx_toggles.toggles.testutils import override_waffle_flag

from openedx.core.djangoapps.user_authn.config.waffle import REDIRECT_TO_LMS


@ddt.ddt
class TestAdminView(TestCase):
    """
    Tests of the admin view.
    """
    @override_waffle_flag(REDIRECT_TO_LMS, True)
    @ddt.data(('/admin/', 3), ('/admin/login', 3), (reverse('admin:login'), 2))
    @ddt.unpack
    def test_admin_login_redirect(self, admin_url, index):
        """Admin login will redirect towards the site login page."""
        response = self.client.get(admin_url, follow=True)
        self.assertIn('/login/edx-oauth2/?next=', response.redirect_chain[index][0])

    def test_admin_login_default(self):
        """Without flag Admin login will redirect towards the admin default login page."""
        response = self.client.get('/admin/', follow=True)
        assert response.status_code == 200
        self.assertIn('/admin/login/?next=/admin/', response.redirect_chain[0])
        assert len(response.redirect_chain) == 1
        assert response.template_name == ['admin/login.html']
