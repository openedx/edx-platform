"""
Tests for support views.
"""

import ddt
from django.test import TestCase
from django.core.urlresolvers import reverse

from student.roles import GlobalStaff, SupportStaffRole
from student.tests.factories import UserFactory


class SupportViewTestCase(TestCase):
    """
    Base class for support view tests.
    """

    USERNAME = "support"
    EMAIL = "support@example.com"
    PASSWORD = "support"

    def setUp(self):
        """Create a user and log in. """
        super(SupportViewTestCase, self).setUp()
        self.user = UserFactory(username=self.USERNAME, email=self.EMAIL, password=self.PASSWORD)
        success = self.client.login(username=self.USERNAME, password=self.PASSWORD)
        self.assertTrue(success, msg="Could not log in")


@ddt.ddt
class SupportViewAccessTests(SupportViewTestCase):
    """
    Tests for access control of support views.
    """

    @ddt.data(
        ("support:index", GlobalStaff, True),
        ("support:index", SupportStaffRole, True),
        ("support:index", None, False),
        ("support:certificates", GlobalStaff, True),
        ("support:certificates", SupportStaffRole, True),
        ("support:certificates", None, False),
        ("support:refund", GlobalStaff, True),
        ("support:refund", SupportStaffRole, True),
        ("support:refund", None, False),
    )
    @ddt.unpack
    def test_access(self, url_name, role, has_access):
        if role is not None:
            role().add_users(self.user)

        url = reverse(url_name)
        response = self.client.get(url)

        if has_access:
            self.assertEqual(response.status_code, 200)
        else:
            self.assertEqual(response.status_code, 403)

    @ddt.data("support:index", "support:certificates", "support:refund")
    def test_require_login(self, url_name):
        url = reverse(url_name)

        # Log out then try to retrieve the page
        self.client.logout()
        response = self.client.get(url)

        # Expect a redirect to the login page
        redirect_url = "{login_url}?next={original_url}".format(
            login_url=reverse("signin_user"),
            original_url=url,
        )
        self.assertRedirects(response, redirect_url)


class SupportViewIndexTests(SupportViewTestCase):
    """
    Tests for the support index view.
    """

    EXPECTED_URL_NAMES = [
        "support:certificates",
        "support:refund",
    ]

    def setUp(self):
        """Make the user support staff. """
        super(SupportViewIndexTests, self).setUp()
        SupportStaffRole().add_users(self.user)

    def test_index(self):
        response = self.client.get(reverse("support:index"))
        self.assertContains(response, "Support")

        # Check that all the expected links appear on the index page.
        for url_name in self.EXPECTED_URL_NAMES:
            self.assertContains(response, reverse(url_name))


class SupportViewCertificatesTests(SupportViewTestCase):
    """
    Tests for the certificates support view.
    """
    def setUp(self):
        """Make the user support staff. """
        super(SupportViewCertificatesTests, self).setUp()
        SupportStaffRole().add_users(self.user)

    def test_certificates_no_query(self):
        # Check that an empty initial query is passed to the JavaScript client correctly.
        response = self.client.get(reverse("support:certificates"))
        self.assertContains(response, "userQuery: ''")

    def test_certificates_with_query(self):
        # Check that an initial query is passed to the JavaScript client.
        url = reverse("support:certificates") + "?query=student@example.com"
        response = self.client.get(url)
        self.assertContains(response, "userQuery: 'student@example.com'")
