"""
Tests for BadgrBackend
"""

import datetime
from unittest.mock import Mock, call, patch

import json
import ddt
import httpretty
from django.test.utils import override_settings
from lazy.lazy import lazy  # lint-amnesty, pylint: disable=no-name-in-module

from edx_django_utils.cache import TieredCache
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from common.djangoapps.track.tests import FROZEN_TIME, EventTrackingTestCase
from lms.djangoapps.badges.backends.badgr import BadgrBackend
from lms.djangoapps.badges.models import BadgeAssertion
from lms.djangoapps.badges.tests.factories import BadgeClassFactory
from openedx.core.lib.tests.assertions.events import assert_event_matches
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.tests.factories import CourseFactory  # lint-amnesty, pylint: disable=wrong-import-order

BADGR_SETTINGS = {
    'BADGR_BASE_URL': 'https://example.com',
    'BADGR_ISSUER_SLUG': 'test-issuer',
    'BADGR_USERNAME': 'example@example.com',
    'BADGR_PASSWORD': 'password',
    'BADGR_TOKENS_CACHE_KEY': 'badgr-test-cache-key'
}

# Should be the hashed result of test_slug as the slug, and test_component as the component
EXAMPLE_SLUG = '9e915d55bb304a73d20c453531d3c27f81574218413c23903823d20d11b587ae'
BADGR_SERVER_SLUG = 'test_badgr_server_slug'


# pylint: disable=protected-access
@ddt.ddt
@override_settings(**BADGR_SETTINGS)
@httpretty.activate
class BadgrBackendTestCase(ModuleStoreTestCase, EventTrackingTestCase):
    """
    Tests the BadgeHandler object
    """

    def setUp(self):
        """
        Create a course and user to test with.
        """
        super().setUp()
        # Need key to be deterministic to test slugs.
        self.course = CourseFactory.create(
            org='edX', course='course_test', run='test_run', display_name='Badged',
            start=datetime.datetime(year=2015, month=5, day=19),
            end=datetime.datetime(year=2015, month=5, day=20)
        )
        self.user = UserFactory.create(email='example@example.com')
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.location.course_key, mode='honor')
        # Need to empty this on each run.
        BadgrBackend.badges = []
        self.badge_class = BadgeClassFactory.create(course_id=self.course.location.course_key)
        self.legacy_badge_class = BadgeClassFactory.create(
            course_id=self.course.location.course_key, issuing_component=''
        )
        self.no_course_badge_class = BadgeClassFactory.create()
        TieredCache.dangerous_clear_all_tiers()
        httpretty.httpretty.reset()

    @lazy
    def handler(self):
        """
        Lazily loads a BadgeHandler object for the current course. Can't do this on setUp because the settings
        overrides aren't in place.
        """
        return BadgrBackend()

    def _mock_badgr_tokens_api(self, result):
        assert httpretty.is_enabled()
        responses = [httpretty.Response(body=json.dumps(result),
                                        content_type='application/json')]
        httpretty.register_uri(httpretty.POST,
                               'https://example.com/o/token',
                               responses=responses)

    def test_urls(self):
        """
        Make sure the handler generates the correct URLs for different API tasks.
        """
        assert self.handler._base_url == 'https://example.com/v2/issuers/test-issuer'
        # lint-amnesty, pylint: disable=no-member
        assert self.handler._badge_create_url == 'https://example.com/v2/issuers/test-issuer/badgeclasses'
        # lint-amnesty, pylint: disable=no-member
        assert self.handler._badge_url('test_slug_here') ==\
               'https://example.com/v2/badgeclasses/test_slug_here'
        assert self.handler._assertion_url('another_test_slug') ==\
               'https://example.com/v2/badgeclasses/another_test_slug/assertions'

    def check_headers(self, headers):
        """
        Verify the a headers dict from a requests call matches the proper auth info.
        """
        assert headers == {'Authorization': 'Bearer 12345'}

    def test_get_headers(self):
        """
        Check to make sure the handler generates appropriate HTTP headers.
        """
        self.handler._get_access_token = Mock(return_value='12345')
        self.check_headers(self.handler._get_headers())  # lint-amnesty, pylint: disable=no-member

    @patch('requests.post')
    def test_create_badge(self, post):
        """
        Verify badge spec creation works.
        """
        self.handler._get_access_token = Mock(return_value='12345')
        with self.allow_transaction_exception():
            self.handler._create_badge(self.badge_class)
        args, kwargs = post.call_args
        assert args[0] == 'https://example.com/v2/issuers/test-issuer/badgeclasses'
        assert kwargs['files']['image'][0] == self.badge_class.image.name
        assert kwargs['files']['image'][2] == 'image/png'
        self.check_headers(kwargs['headers'])
        assert kwargs['data'] ==\
               {'name': 'Test Badge',
                'criteriaUrl': 'https://example.com/syllabus',
                'description': "Yay! It's a test badge."}

    def test_ensure_badge_created_cache(self):
        """
        Make sure ensure_badge_created doesn't call create_badge if we know the badge is already there.
        """
        BadgrBackend.badges.append(BADGR_SERVER_SLUG)
        self.handler._create_badge = Mock()
        self.handler._ensure_badge_created(self.badge_class)  # lint-amnesty, pylint: disable=no-member
        assert not self.handler._create_badge.called

    @ddt.unpack
    @ddt.data(
        ('badge_class', EXAMPLE_SLUG),
        ('legacy_badge_class', 'test_slug'),
        ('no_course_badge_class', 'test_componenttest_slug')
    )
    def test_slugs(self, badge_class_type, slug):
        assert self.handler._slugify(getattr(self, badge_class_type)) == slug
        # lint-amnesty, pylint: disable=no-member

    @patch('requests.get')
    def test_ensure_badge_created_checks(self, get):
        response = Mock()
        response.status_code = 200
        get.return_value = response
        assert 'test_componenttest_slug' not in BadgrBackend.badges
        self.handler._get_access_token = Mock(return_value='12345')
        self.handler._create_badge = Mock()
        self.handler._ensure_badge_created(self.badge_class)  # lint-amnesty, pylint: disable=no-member
        assert get.called
        args, kwargs = get.call_args
        assert args[0] == (
            'https://example.com/v2/badgeclasses/' +
            BADGR_SERVER_SLUG)
        self.check_headers(kwargs['headers'])
        assert BADGR_SERVER_SLUG in BadgrBackend.badges
        assert not self.handler._create_badge.called

    @patch('requests.get')
    def test_ensure_badge_created_creates(self, get):
        response = Mock()
        response.status_code = 404
        get.return_value = response
        assert BADGR_SERVER_SLUG not in BadgrBackend.badges
        self.handler._get_access_token = Mock(return_value='12345')
        self.handler._create_badge = Mock()
        self.handler._ensure_badge_created(self.badge_class)  # lint-amnesty, pylint: disable=no-member
        assert self.handler._create_badge.called
        assert self.handler._create_badge.call_args == call(self.badge_class)
        assert BADGR_SERVER_SLUG in BadgrBackend.badges

    @patch('requests.post')
    def test_badge_creation_event(self, post):
        result = {
            'result': [{
                'openBadgeId': 'http://www.example.com/example',
                'image': 'http://www.example.com/example.png',
                'issuer': 'https://example.com/v2/issuers/test-issuer'
            }]
        }
        response = Mock()
        response.json.return_value = result
        post.return_value = response
        self.recreate_tracker()
        self.handler._get_access_token = Mock(return_value='12345')
        self.handler._create_assertion(self.badge_class, self.user, 'https://example.com/irrefutable_proof')  # lint-amnesty, pylint: disable=no-member
        args, kwargs = post.call_args
        assert args[0] == ((
            'https://example.com/v2/badgeclasses/' +
            BADGR_SERVER_SLUG) +
            '/assertions')
        self.check_headers(kwargs['headers'])
        assertion = BadgeAssertion.objects.get(user=self.user, badge_class__course_id=self.course.location.course_key)
        assert assertion.data == result['result'][0]
        assert assertion.image_url == 'http://www.example.com/example.png'
        assert assertion.assertion_url == 'http://www.example.com/example'
        assert kwargs['json'] == {"recipient": {"identity": 'example@example.com', "type": "email"},
                                  "evidence": [{"url": 'https://example.com/irrefutable_proof'}],
                                  "notify": False}
        assert_event_matches({
            'name': 'edx.badge.assertion.created',
            'data': {
                'user_id': self.user.id,
                'course_id': str(self.course.location.course_key),
                'enrollment_mode': 'honor',
                'assertion_id': assertion.id,
                'badge_name': 'Test Badge',
                'badge_slug': 'test_slug',
                'badge_badgr_server_slug': BADGR_SERVER_SLUG,
                'issuing_component': 'test_component',
                'assertion_image_url': 'http://www.example.com/example.png',
                'assertion_json_url': 'http://www.example.com/example',
                'issuer': 'https://example.com/v2/issuers/test-issuer',
            },
            'context': {},
            'timestamp': FROZEN_TIME
        }, self.get_event())

    def test_get_new_tokens(self):
        result = {
            'access_token': '12345',
            'refresh_token': '67890',
            'expires_in': 86400,
        }
        self._mock_badgr_tokens_api(result)
        self.handler._get_and_cache_oauth_tokens()
        assert 'o/token' in httpretty.httpretty.last_request.path
        assert httpretty.httpretty.last_request.parsed_body == {
            'username': ['example@example.com'],
            'password': ['password']}

    def test_renew_tokens(self):
        result = {
            'access_token': '12345',
            'refresh_token': '67890',
            'expires_in': 86400,
        }
        self._mock_badgr_tokens_api(result)
        self.handler._get_and_cache_oauth_tokens(refresh_token='67890')
        assert 'o/token' in httpretty.httpretty.last_request.path
        assert httpretty.httpretty.last_request.parsed_body == {
            'grant_type': ['refresh_token'],
            'refresh_token': ['67890']}

    def test_get_access_token_from_cache_valid(self):
        encrypted_access_token = self.handler._encrypt_token('12345')
        encrypted_refresh_token = self.handler._encrypt_token('67890')
        tokens = {
            'access_token': encrypted_access_token,
            'refresh_token': encrypted_refresh_token,
            'expires_at': datetime.datetime.utcnow() + datetime.timedelta(seconds=20)
        }
        TieredCache.set_all_tiers('badgr-test-cache-key', tokens, None)

        access_token = self.handler._get_access_token()
        assert access_token == self.handler._decrypt_token(
            tokens.get('access_token'))

    def test_get_access_token_from_cache_expired(self):
        encrypted_access_token = self.handler._encrypt_token('12345')
        encrypted_refresh_token = self.handler._encrypt_token('67890')
        tokens = {
            'access_token': encrypted_access_token,
            'refresh_token': encrypted_refresh_token,
            'expires_at': datetime.datetime.utcnow()
        }
        TieredCache.set_all_tiers('badgr-test-cache-key', tokens, None)
        result = {
            'access_token': '12345',
            'refresh_token': '67890',
            'expires_in': 86400,
        }
        self._mock_badgr_tokens_api(result)
        access_token = self.handler._get_access_token()
        assert access_token == result.get('access_token')
        assert 'o/token' in httpretty.httpretty.last_request.path
        assert httpretty.httpretty.last_request.parsed_body == {
            'grant_type': ['refresh_token'],
            'refresh_token': [self.handler._decrypt_token(
                tokens.get('refresh_token'))]}

    def test_get_access_token_from_cache_none(self):
        result = {
            'access_token': '12345',
            'refresh_token': '67890',
            'expires_in': 86400,
        }
        self._mock_badgr_tokens_api(result)
        access_token = self.handler._get_access_token()
        assert access_token == result.get('access_token')
        assert 'o/token' in httpretty.httpretty.last_request.path
        assert httpretty.httpretty.last_request.parsed_body == {
            'username': ['example@example.com'],
            'password': ['password']}
