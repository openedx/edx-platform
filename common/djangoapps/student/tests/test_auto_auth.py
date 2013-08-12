from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from util.testing import UrlResetMixin
from mock import patch
from django.core.urlresolvers import reverse, NoReverseMatch


class AutoAuthEnabledTestCase(UrlResetMixin, TestCase):
    """
    Tests for the Auto auth view that we have for load testing.
    """

    @patch.dict("django.conf.settings.MITX_FEATURES", {"AUTOMATIC_AUTH_FOR_TESTING": True})
    def setUp(self):
        # Patching the settings.MITX_FEATURES['AUTOMATIC_AUTH_FOR_TESTING']
        # value affects the contents of urls.py,
        # so we need to call super.setUp() which reloads urls.py (because
        # of the UrlResetMixin)
        super(AutoAuthEnabledTestCase, self).setUp()
        self.url = '/auto_auth'
        self.cms_csrf_url = "signup"
        self.lms_csrf_url = "signin_user"
        self.client = Client()

    def test_create_user(self):
        """
        Test that user gets created when visiting the page.
        """

        self.client.get(self.url)

        qset = User.objects.all()

        # assert user was created and is active
        self.assertEqual(qset.count(), 1)
        user = qset[0]
        assert user.is_active

    def test_create_defined_user(self):
        """
        Test that the user gets created with the correct attributes
        when they are passed as parameters on the auto-auth page.
        """

        self.client.get(
            self.url,
            {'username': 'robot', 'password': 'test', 'email': 'robot@edx.org'}
        )

        qset = User.objects.all()

        # assert user was created with the correct username and password
        self.assertEqual(qset.count(), 1)
        user = qset[0]
        self.assertEqual(user.username, 'robot')
        self.assertTrue(user.check_password('test'))
        self.assertEqual(user.email, 'robot@edx.org')

    @patch('student.views.random.randint')
    def test_create_multiple_users(self, randint):
        """
        Test to make sure multiple users are created.
        """
        randint.return_value = 1
        self.client.get(self.url)

        randint.return_value = 2
        self.client.get(self.url)

        qset = User.objects.all()

        # make sure that USER_1 and USER_2 were created correctly
        self.assertEqual(qset.count(), 2)
        user1 = qset[0]
        self.assertEqual(user1.username, 'USER_1')
        self.assertTrue(user1.check_password('PASS_1'))
        self.assertEqual(user1.email, 'USER_1_dummy_test@mitx.mit.edu')
        self.assertEqual(qset[1].username, 'USER_2')

    @patch.dict("django.conf.settings.MITX_FEATURES", {"MAX_AUTO_AUTH_USERS": 1})
    def test_login_already_created_user(self):
        """
        Test that when we have reached the limit for automatic users
        a subsequent request results in an already existant one being
        logged in.
        """
        # auto-generate 1 user (the max)
        url = '/auto_auth'
        self.client.get(url)

        # go to the site again
        self.client.get(url)
        qset = User.objects.all()

        # make sure it is the same user
        self.assertEqual(qset.count(), 1)


class AutoAuthDisabledTestCase(UrlResetMixin, TestCase):
    """
    Test that the page is inaccessible with default settings
    """

    @patch.dict("django.conf.settings.MITX_FEATURES", {"AUTOMATIC_AUTH_FOR_TESTING": False})
    def setUp(self):
        # Patching the settings.MITX_FEATURES['AUTOMATIC_AUTH_FOR_TESTING']
        # value affects the contents of urls.py,
        # so we need to call super.setUp() which reloads urls.py (because
        # of the UrlResetMixin)
        super(AutoAuthDisabledTestCase, self).setUp()
        self.url = '/auto_auth'
        self.client = Client()

    def test_auto_auth_disabled(self):
        """
        Make sure automatic authentication is disabled.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_csrf_enabled(self):
        """
        test that when not load testing, csrf protection is on
        """
        cms_csrf_url = "signup"
        lms_csrf_url = "signin_user"
        self.client = Client(enforce_csrf_checks=True)
        try:
            csrf_protected_url = reverse(cms_csrf_url)
            response = self.client.post(csrf_protected_url)
        except NoReverseMatch:
            csrf_protected_url = reverse(lms_csrf_url)
            response = self.client.post(csrf_protected_url)

        self.assertEqual(response.status_code, 403)
