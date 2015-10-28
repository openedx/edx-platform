"""
Tests for the BadgeHandler, which communicates with the Badgr Server.
"""
from datetime import datetime
from django.test.utils import override_settings
from django.db.models.fields.files import ImageFieldFile
from lazy.lazy import lazy
from mock import patch, Mock, call
from certificates.models import BadgeAssertion, BadgeImageConfiguration
from openedx.core.lib.tests.assertions.events import assert_event_matches
from track.tests import EventTrackingTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from certificates.badge_handler import BadgeHandler
from certificates.tests.factories import BadgeImageConfigurationFactory
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

BADGR_SETTINGS = {
    'BADGR_API_TOKEN': '12345',
    'BADGR_BASE_URL': 'https://example.com',
    'BADGR_ISSUER_SLUG': 'test-issuer',
}


@override_settings(**BADGR_SETTINGS)
class BadgeHandlerTestCase(ModuleStoreTestCase, EventTrackingTestCase):
    """
    Tests the BadgeHandler object
    """
    def setUp(self):
        """
        Create a course and user to test with.
        """
        super(BadgeHandlerTestCase, self).setUp()
        # Need key to be deterministic to test slugs.
        self.course = CourseFactory.create(
            org='edX', course='course_test', run='test_run', display_name='Badged',
            start=datetime(year=2015, month=5, day=19),
            end=datetime(year=2015, month=5, day=20)
        )
        self.user = UserFactory.create(email='example@example.com')
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.location.course_key, mode='honor')
        # Need for force empty this dict on each run.
        BadgeHandler.badges = {}
        BadgeImageConfigurationFactory()

    @lazy
    def handler(self):
        """
        Lazily loads a BadgeHandler object for the current course. Can't do this on setUp because the settings
        overrides aren't in place.
        """
        return BadgeHandler(self.course.location.course_key)

    def test_urls(self):
        """
        Make sure the handler generates the correct URLs for different API tasks.
        """
        self.assertEqual(self.handler.base_url, 'https://example.com/v1/issuer/issuers/test-issuer')
        self.assertEqual(self.handler.badge_create_url, 'https://example.com/v1/issuer/issuers/test-issuer/badges')
        self.assertEqual(
            self.handler.badge_url('honor'),
            'https://example.com/v1/issuer/issuers/test-issuer/badges/edxcourse_testtest_run_honor_fc5519b'
        )
        self.assertEqual(
            self.handler.assertion_url('honor'),
            'https://example.com/v1/issuer/issuers/test-issuer/badges/edxcourse_testtest_run_honor_fc5519b/assertions'
        )

    def check_headers(self, headers):
        """
        Verify the a headers dict from a requests call matches the proper auth info.
        """
        self.assertEqual(headers, {'Authorization': 'Token 12345'})

    def test_slug(self):
        """
        Verify slug generation is working as expected. If this test fails, the algorithm has changed, and it will cause
        the handler to lose track of all badges it made in the past.
        """
        self.assertEqual(
            self.handler.course_slug('honor'),
            'edxcourse_testtest_run_honor_fc5519b'
        )
        self.assertEqual(
            self.handler.course_slug('verified'),
            'edxcourse_testtest_run_verified_a199ec0'
        )

    def test_get_headers(self):
        """
        Check to make sure the handler generates appropriate HTTP headers.
        """
        self.check_headers(self.handler.get_headers())

    @patch('requests.post')
    def test_create_badge(self, post):
        """
        Verify badge spec creation works.
        """
        self.handler.create_badge('honor')
        args, kwargs = post.call_args
        self.assertEqual(args[0], 'https://example.com/v1/issuer/issuers/test-issuer/badges')
        self.assertEqual(kwargs['files']['image'][0], BadgeImageConfiguration.objects.get(mode='honor').icon.name)
        self.assertIsInstance(kwargs['files']['image'][1], ImageFieldFile)
        self.assertEqual(kwargs['files']['image'][2], 'image/png')
        self.check_headers(kwargs['headers'])
        self.assertEqual(
            kwargs['data'],
            {
                'name': 'Badged',
                'slug': 'edxcourse_testtest_run_honor_fc5519b',
                'criteria': 'https://edx.org/courses/edX/course_test/test_run/about',
                'description': 'Completed the course "Badged" (honor, 2015-05-19 - 2015-05-20)',
            }
        )

    def test_self_paced_description(self):
        """
        Verify that a badge created for a course with no end date gets a different description.
        """
        self.course.end = None
        self.assertEqual(BadgeHandler.badge_description(self.course, 'honor'), 'Completed the course "Badged" (honor)')

    def test_ensure_badge_created_cache(self):
        """
        Make sure ensure_badge_created doesn't call create_badge if we know the badge is already there.
        """
        BadgeHandler.badges['edxcourse_testtest_run_honor_fc5519b'] = True
        self.handler.create_badge = Mock()
        self.handler.ensure_badge_created('honor')
        self.assertFalse(self.handler.create_badge.called)

    @patch('requests.get')
    def test_ensure_badge_created_checks(self, get):
        response = Mock()
        response.status_code = 200
        get.return_value = response
        self.assertNotIn('edxcourse_testtest_run_honor_fc5519b', BadgeHandler.badges)
        self.handler.create_badge = Mock()
        self.handler.ensure_badge_created('honor')
        self.assertTrue(get.called)
        args, kwargs = get.call_args
        self.assertEqual(
            args[0],
            'https://example.com/v1/issuer/issuers/test-issuer/badges/'
            'edxcourse_testtest_run_honor_fc5519b'
        )
        self.check_headers(kwargs['headers'])
        self.assertTrue(BadgeHandler.badges['edxcourse_testtest_run_honor_fc5519b'])
        self.assertFalse(self.handler.create_badge.called)

    @patch('requests.get')
    def test_ensure_badge_created_creates(self, get):
        response = Mock()
        response.status_code = 404
        get.return_value = response
        self.assertNotIn('edxcourse_testtest_run_honor_fc5519b', BadgeHandler.badges)
        self.handler.create_badge = Mock()
        self.handler.ensure_badge_created('honor')
        self.assertTrue(self.handler.create_badge.called)
        self.assertEqual(self.handler.create_badge.call_args, call('honor'))
        self.assertTrue(BadgeHandler.badges['edxcourse_testtest_run_honor_fc5519b'])

    @patch('requests.post')
    def test_badge_creation_event(self, post):
        result = {
            'json': {'id': 'http://www.example.com/example'},
            'image': 'http://www.example.com/example.png',
            'slug': 'test_assertion_slug',
            'issuer': 'https://example.com/v1/issuer/issuers/test-issuer',
        }
        response = Mock()
        response.json.return_value = result
        post.return_value = response
        self.recreate_tracker()
        self.handler.create_assertion(self.user, 'honor')
        args, kwargs = post.call_args
        self.assertEqual(
            args[0],
            'https://example.com/v1/issuer/issuers/test-issuer/badges/'
            'edxcourse_testtest_run_honor_fc5519b/assertions'
        )
        self.check_headers(kwargs['headers'])
        assertion = BadgeAssertion.objects.get(user=self.user, course_id=self.course.location.course_key)
        self.assertEqual(assertion.data, result)
        self.assertEqual(assertion.image_url, 'http://www.example.com/example.png')
        self.assertEqual(kwargs['data'], {
            'email': 'example@example.com',
            'evidence': 'https://edx.org/certificates/user/2/course/edX/course_test/test_run?evidence_visit=1'
        })
        assert_event_matches({
            'name': 'edx.badge.assertion.created',
            'data': {
                'user_id': self.user.id,
                'course_id': unicode(self.course.location.course_key),
                'enrollment_mode': 'honor',
                'assertion_id': assertion.id,
                'assertion_image_url': 'http://www.example.com/example.png',
                'assertion_json_url': 'http://www.example.com/example',
                'issuer': 'https://example.com/v1/issuer/issuers/test-issuer',
            }
        }, self.get_event())
