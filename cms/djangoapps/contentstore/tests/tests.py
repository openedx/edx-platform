"""
This test file will test registration, login, activation, and session activity timeouts
"""
import time
import mock
import unittest
from ddt import ddt, data, unpack

from django.test import TestCase
from django.test.utils import override_settings
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from contentstore.models import PushNotificationConfig
from contentstore.tests.utils import parse_json, user, registration, AjaxEnabledTestClient
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from contentstore.tests.test_course_settings import CourseTestCase
from xmodule.modulestore.tests.factories import CourseFactory
import datetime
from pytz import UTC

from freezegun import freeze_time


class ContentStoreTestCase(ModuleStoreTestCase):
    def _login(self, email, password):
        """
        Login.  View should always return 200.  The success/fail is in the
        returned json
        """
        resp = self.client.post(
            reverse('login_post'),
            {'email': email, 'password': password}
        )
        self.assertEqual(resp.status_code, 200)
        return resp

    def login(self, email, password):
        """Login, check that it worked."""
        resp = self._login(email, password)
        data = parse_json(resp)
        self.assertTrue(data['success'])
        return resp

    def _create_account(self, username, email, password):
        """Try to create an account.  No error checking"""
        resp = self.client.post('/create_account', {
            'username': username,
            'email': email,
            'password': password,
            'location': 'home',
            'language': 'Franglish',
            'name': 'Fred Weasley',
            'terms_of_service': 'true',
            'honor_code': 'true',
        })
        return resp

    def create_account(self, username, email, password):
        """Create the account and check that it worked"""
        resp = self._create_account(username, email, password)
        self.assertEqual(resp.status_code, 200)
        data = parse_json(resp)
        self.assertEqual(data['success'], True)

        # Check both that the user is created, and inactive
        self.assertFalse(user(email).is_active)

        return resp

    def _activate_user(self, email):
        """Look up the activation key for the user, then hit the activate view.
        No error checking"""
        activation_key = registration(email).activation_key

        # and now we try to activate
        resp = self.client.get(reverse('activate', kwargs={'key': activation_key}))
        return resp

    def activate_user(self, email):
        resp = self._activate_user(email)
        self.assertEqual(resp.status_code, 200)
        # Now make sure that the user is now actually activated
        self.assertTrue(user(email).is_active)


class AuthTestCase(ContentStoreTestCase):
    """Check that various permissions-related things work"""

    CREATE_USER = False
    ENABLED_CACHES = ['default', 'mongo_metadata_inheritance', 'loc_cache']

    def setUp(self):
        super(AuthTestCase, self).setUp()

        self.email = 'a@b.com'
        self.pw = 'xyz'
        self.username = 'testuser'
        self.client = AjaxEnabledTestClient()
        # clear the cache so ratelimiting won't affect these tests
        cache.clear()

    def check_page_get(self, url, expected):
        resp = self.client.get_html(url)
        self.assertEqual(resp.status_code, expected)
        return resp

    def test_public_pages_load(self):
        """Make sure pages that don't require login load without error."""
        pages = (
            reverse('login'),
            reverse('signup'),
        )
        for page in pages:
            print "Checking '{0}'".format(page)
            self.check_page_get(page, 200)

    def test_create_account_errors(self):
        # No post data -- should fail
        resp = self.client.post('/create_account', {})
        self.assertEqual(resp.status_code, 400)
        data = parse_json(resp)
        self.assertEqual(data['success'], False)

    def test_create_account(self):
        self.create_account(self.username, self.email, self.pw)
        self.activate_user(self.email)

    def test_create_account_username_already_exists(self):
        User.objects.create_user(self.username, self.email, self.pw)
        resp = self._create_account(self.username, "abc@def.com", "password")
        # we have a constraint on unique usernames, so this should fail
        self.assertEqual(resp.status_code, 400)

    def test_create_account_pw_already_exists(self):
        User.objects.create_user(self.username, self.email, self.pw)
        resp = self._create_account("abcdef", "abc@def.com", self.pw)
        # we can have two users with the same password, so this should succeed
        self.assertEqual(resp.status_code, 200)

    @unittest.skipUnless(settings.SOUTH_TESTS_MIGRATE, "South migrations required")
    def test_create_account_email_already_exists(self):
        User.objects.create_user(self.username, self.email, self.pw)
        resp = self._create_account("abcdef", self.email, "password")
        # This is tricky. Django's user model doesn't have a constraint on
        # unique email addresses, but we *add* that constraint during the
        # migration process:
        # see common/djangoapps/student/migrations/0004_add_email_index.py
        #
        # The behavior we *want* is for this account creation request
        # to fail, due to this uniqueness constraint, but the request will
        # succeed if the migrations have not run.
        self.assertEqual(resp.status_code, 400)

    def test_login(self):
        self.create_account(self.username, self.email, self.pw)

        # Not activated yet.  Login should fail.
        resp = self._login(self.email, self.pw)
        data = parse_json(resp)
        self.assertFalse(data['success'])

        self.activate_user(self.email)

        # Now login should work
        self.login(self.email, self.pw)

    def test_login_ratelimited(self):
        # try logging in 30 times, the default limit in the number of failed
        # login attempts in one 5 minute period before the rate gets limited
        for i in xrange(30):
            resp = self._login(self.email, 'wrong_password{0}'.format(i))
            self.assertEqual(resp.status_code, 200)
        resp = self._login(self.email, 'wrong_password')
        self.assertEqual(resp.status_code, 200)
        data = parse_json(resp)
        self.assertFalse(data['success'])
        self.assertIn('Too many failed login attempts.', data['value'])

    @override_settings(MAX_FAILED_LOGIN_ATTEMPTS_ALLOWED=3)
    @override_settings(MAX_FAILED_LOGIN_ATTEMPTS_LOCKOUT_PERIOD_SECS=2)
    def test_excessive_login_failures(self):
        # try logging in 3 times, the account should get locked for 3 seconds
        # note we want to keep the lockout time short, so we don't slow down the tests

        with mock.patch.dict('django.conf.settings.FEATURES', {'ENABLE_MAX_FAILED_LOGIN_ATTEMPTS': True}):
            self.create_account(self.username, self.email, self.pw)
            self.activate_user(self.email)

            for i in xrange(3):
                resp = self._login(self.email, 'wrong_password{0}'.format(i))
                self.assertEqual(resp.status_code, 200)
                data = parse_json(resp)
                self.assertFalse(data['success'])
                self.assertIn(
                    'Email or password is incorrect.',
                    data['value']
                )

            # now the account should be locked

            resp = self._login(self.email, 'wrong_password')
            self.assertEqual(resp.status_code, 200)
            data = parse_json(resp)
            self.assertFalse(data['success'])
            self.assertIn(
                'This account has been temporarily locked due to excessive login failures. Try again later.',
                data['value']
            )

            with freeze_time('2100-01-01'):
                self.login(self.email, self.pw)

            # make sure the failed attempt counter gets reset on successful login
            resp = self._login(self.email, 'wrong_password')
            self.assertEqual(resp.status_code, 200)
            data = parse_json(resp)
            self.assertFalse(data['success'])

            # account should not be locked out after just one attempt
            self.login(self.email, self.pw)

            # do one more login when there is no bad login counter row at all in the database to
            # test the "ObjectNotFound" case
            self.login(self.email, self.pw)

    def test_login_link_on_activation_age(self):
        self.create_account(self.username, self.email, self.pw)
        # we want to test the rendering of the activation page when the user isn't logged in
        self.client.logout()
        resp = self._activate_user(self.email)
        self.assertEqual(resp.status_code, 200)

        # check the the HTML has links to the right login page. Note that this is merely a content
        # check and thus could be fragile should the wording change on this page
        expected = 'You can now <a href="' + reverse('login') + '">sign in</a>.'
        self.assertIn(expected, resp.content)

    def test_private_pages_auth(self):
        """Make sure pages that do require login work."""
        auth_pages = (
            '/home/',
        )

        # These are pages that should just load when the user is logged in
        # (no data needed)
        simple_auth_pages = (
            '/home/',
        )

        # need an activated user
        self.test_create_account()

        # Create a new session
        self.client = AjaxEnabledTestClient()

        # Not logged in.  Should redirect to login.
        print 'Not logged in'
        for page in auth_pages:
            print "Checking '{0}'".format(page)
            self.check_page_get(page, expected=302)

        # Logged in should work.
        self.login(self.email, self.pw)

        print 'Logged in'
        for page in simple_auth_pages:
            print "Checking '{0}'".format(page)
            self.check_page_get(page, expected=200)

    def test_index_auth(self):

        # not logged in.  Should return a redirect.
        resp = self.client.get_html('/home/')
        self.assertEqual(resp.status_code, 302)

        # Logged in should work.

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=1)
    def test_inactive_session_timeout(self):
        """
        Verify that an inactive session times out and redirects to the
        login page
        """
        self.create_account(self.username, self.email, self.pw)
        self.activate_user(self.email)

        self.login(self.email, self.pw)

        # make sure we can access courseware immediately
        course_url = '/home/'
        resp = self.client.get_html(course_url)
        self.assertEquals(resp.status_code, 200)

        # then wait a bit and see if we get timed out
        time.sleep(2)

        resp = self.client.get_html(course_url)

        # re-request, and we should get a redirect to login page
        self.assertRedirects(resp, settings.LOGIN_REDIRECT_URL + '?next=/home/')


class ForumTestCase(CourseTestCase):
    def setUp(self):
        """ Creates the test course. """
        super(ForumTestCase, self).setUp()
        self.course = CourseFactory.create(org='testX', number='727', display_name='Forum Course')

    def test_blackouts(self):
        now = datetime.datetime.now(UTC)
        times1 = [
            (now - datetime.timedelta(days=14), now - datetime.timedelta(days=11)),
            (now + datetime.timedelta(days=24), now + datetime.timedelta(days=30))
        ]
        self.course.discussion_blackouts = [(t.isoformat(), t2.isoformat()) for t, t2 in times1]
        self.assertTrue(self.course.forum_posts_allowed)
        times2 = [
            (now - datetime.timedelta(days=14), now + datetime.timedelta(days=2)),
            (now + datetime.timedelta(days=24), now + datetime.timedelta(days=30))
        ]
        self.course.discussion_blackouts = [(t.isoformat(), t2.isoformat()) for t, t2 in times2]
        self.assertFalse(self.course.forum_posts_allowed)

        # test if user gives empty blackout date it should return true for forum_posts_allowed
        self.course.discussion_blackouts = [[]]
        self.assertTrue(self.course.forum_posts_allowed)


@ddt
class CourseKeyVerificationTestCase(CourseTestCase):
    def setUp(self):
        """
        Create test course.
        """
        super(CourseKeyVerificationTestCase, self).setUp()
        self.course = CourseFactory.create(org='edX', number='test_course_key', display_name='Test Course')

    @data(('edX/test_course_key/Test_Course', 200), ('garbage:edX+test_course_key+Test_Course', 404))
    @unpack
    def test_course_key_decorator(self, course_key, status_code):
        """
        Tests for the ensure_valid_course_key decorator.
        """
        url = '/import/{course_key}'.format(course_key=course_key)
        resp = self.client.get_html(url)
        self.assertEqual(resp.status_code, status_code)

        url = '/import_status/{course_key}/{filename}'.format(
            course_key=course_key,
            filename='xyz.tar.gz'
        )
        resp = self.client.get_html(url)
        self.assertEqual(resp.status_code, status_code)


class PushNotificationConfigTestCase(TestCase):
    """
    Tests PushNotificationConfig.
    """
    def test_notifications_defaults(self):
        self.assertFalse(PushNotificationConfig.is_enabled())

    def test_notifications_enabled(self):
        PushNotificationConfig(enabled=True).save()
        self.assertTrue(PushNotificationConfig.is_enabled())
