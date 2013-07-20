from django.test import TestCase
from util.testing import UrlResetMixin
from django.contrib.auth.models import User
from mock import patch


class TestAutoAuthEnabled(UrlResetMixin, TestCase):
    """
    Tests for the Auto auth view that we have for load testing.
    """

    @patch.dict("django.conf.settings.MITX_FEATURES", {"AUTOMATIC_AUTH_FOR_LOAD_TESTING": True})
    def setUp(self):
        # Patching the settings.MITX_FEATURES['AUTOMATIC_AUTH_FOR_LOAD_TESTING']
        # value affects the contents of urls.py,
        # so we need to call super.setUp() which reloads urls.py (because
        # of the UrlResetMixin)
        super(TestAutoAuthEnabled, self).setUp()

    def test_create_user(self):
        """
        tests that user gets created when visiting the page
        """

        url = '/auto_auth'
        self.client.get(url)

        qset = User.objects.all()

        # assert user was created and is active
        self.assertEqual(qset.count(), 1)
        user = qset[0]
        assert user.is_active

    @patch.dict("django.conf.settings.MITX_FEATURES", {"MAX_AUTO_AUTH_USERS": 10000000})
    def test_create_multiple_users(self):
        """
        speculative test to make sure multiple users are created.
        Technically, this test is probabalistic.

        However, my judgement is that if the chance of failing due
        only to bad luck is less than 1:10^1000, we are OK (it is more
        likely that the test failed because the jenkins server was hit
        by an asteroid, or the person running the tests was a freind
        of Hamlet's).
        """

        url = '/auto_auth'

        # hit the url a few times
        # mathematically, is much more efficient
        # to hit the site many many times, and
        # have a smaller MAX user count, but it is
        # the GET request that actually takes a lot
        # of time.
        for i in range(200):
            self.client.get(url)

        qset = User.objects.all()

        # make sure it is the smae user
        self.assertGreater(qset.count(), 1)

    @patch.dict("django.conf.settings.MITX_FEATURES", {"MAX_AUTO_AUTH_USERS": 1})
    def test_login(self):
        """
        test that when we have reached the limit for automatic users
        a subsequent request results in an already existant one being
        logged in.
        """

        # auto-generate 1 user (the max)
        url = '/auto_auth'
        self.client.get(url)

        # go to the site again
        self.client.get(url)
        qset = User.objects.all()

        # make sure it is the smae user
        self.assertEqual(qset.count(), 1)


class TestAutoAuthDisabled(UrlResetMixin, TestCase):
    """
    Test that the page is inaccessible with default settings
    """

    @patch.dict("django.conf.settings.MITX_FEATURES", {"AUTOMATIC_AUTH_FOR_LOAD_TESTING": False})
    def setUp(self):
        # Patching the settings.MITX_FEATURES['AUTOMATIC_AUTH_FOR_LOAD_TESTING']
        # value affects the contents of urls.py,
        # so we need to call super.setUp() which reloads urls.py (because
        # of the UrlResetMixin)
        super(TestAutoAuthDisabled, self).setUp()

    def test_404(self):
        """
        make sure automatic authentication is invisible
        """

        url = '/auto_auth'
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
