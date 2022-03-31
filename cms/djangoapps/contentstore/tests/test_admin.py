"""
Tests that verify that the admin view loads.

This is not inside a django app because it is a global property of the system.
"""
import ddt
from django.test import TestCase
from django.urls import reverse


@ddt.ddt
class TestAdminView(TestCase):
    """
    Tests of the admin view.
    """
    @ddt.data('/admin/', '/admin/login', reverse('admin:login'))
    def test_admin_login_redirect(self, admin_url):
        """Admin login will redirect towards the site login page."""
        response = self.client.get(admin_url, follow=True)
        assert any('/login/edx-oauth2/?next=' in r[0] for r in response.redirect_chain)
