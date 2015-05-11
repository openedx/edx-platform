"""
Tests for the BadgeHandler, which communicates with the Badgr Server.
"""
from django.test.utils import override_settings
from lazy.lazy import lazy
from mock import patch, Mock, call
from certificates.models import BadgeAssertion
from xmodule.modulestore.tests.factories import CourseFactory
from certificates.badge_handler import BadgeHandler
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, TEST_DATA_DIR

BADGR_SETTINGS = {
    'BADGR_API_TOKEN': '12345',
    'BADGR_BASE_URL': 'https://example.com',
    'BADGR_ISSUER_SLUG': 'test-issuer',
    'BADGR_IMAGE_SOURCES': {
        'honor': TEST_DATA_DIR / "badges" / "bulb.svg"
    }
}


@override_settings(**BADGR_SETTINGS)
class BadgeHandlerTestCase(ModuleStoreTestCase):
    """
    Tests the BadgeHandler object
    """
    def setUp(self):
        """
        Create a course and user to test with.
        """
        super(BadgeHandlerTestCase, self).setUp()
        # Need key to be deterministic to test slugs.
        self.course = CourseFactory.create(org='edX', course='course_test', run='test_run', display_name='Badged')
        self.user = UserFactory.create(email='example@example.com')
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.location.course_key, mode='honor')
        # Need for force empty this dict on each run.
        BadgeHandler.badges = {}

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
            'https://example.com/v1/issuer/issuers/test-issuer/badges/'
            'fc5519bfbeff40a53dc6d36a894f5c468c7020edc3858cb86046bc8740c9c1f0'
        )
        self.assertEqual(
            self.handler.assertion_url('honor'),
            'https://example.com/v1/issuer/issuers/test-issuer/badges/'
            'fc5519bfbeff40a53dc6d36a894f5c468c7020edc3858cb86046bc8740c9c1f0/assertions'
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
            'fc5519bfbeff40a53dc6d36a894f5c468c7020edc3858cb86046bc8740c9c1f0'
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
        self.assertEqual(kwargs['files']['image'][0], BADGR_SETTINGS['BADGR_IMAGE_SOURCES']['honor'])
        self.assertIsInstance(kwargs['files']['image'][1], file)
        self.assertEqual(kwargs['files']['image'][2], 'image/svg+xml')
        self.check_headers(kwargs['headers'])
        self.assertEqual(
            kwargs['data'],
            {
                'name': 'Badged',
                'slug': 'fc5519bfbeff40a53dc6d36a894f5c468c7020edc3858cb86046bc8740c9c1f0',
                'criteria': 'http://example.com/courses/edX/course_test/test_run/about',
            }
        )

    def test_ensure_badge_created_cache(self):
        """
        Make sure ensure_badge_created doesn't call create_badge if we know the badge is already there.
        """
        BadgeHandler.badges['fc5519bfbeff40a53dc6d36a894f5c468c7020edc3858cb86046bc8740c9c1f0'] = True
        self.handler.create_badge = Mock()
        self.handler.ensure_badge_created('honor')
        self.assertFalse(self.handler.create_badge.called)

    @patch('requests.get')
    def test_ensure_badge_created_checks(self, get):
        response = Mock()
        response.status_code = 200
        get.return_value = response
        self.assertNotIn('fc5519bfbeff40a53dc6d36a894f5c468c7020edc3858cb86046bc8740c9c1f0', BadgeHandler.badges)
        self.handler.create_badge = Mock()
        self.handler.ensure_badge_created('honor')
        self.assertTrue(get.called)
        args, kwargs = get.call_args
        self.assertEqual(
            args[0],
            'https://example.com/v1/issuer/issuers/test-issuer/badges/'
            'fc5519bfbeff40a53dc6d36a894f5c468c7020edc3858cb86046bc8740c9c1f0'
        )
        self.check_headers(kwargs['headers'])
        self.assertTrue(BadgeHandler.badges['fc5519bfbeff40a53dc6d36a894f5c468c7020edc3858cb86046bc8740c9c1f0'])
        self.assertFalse(self.handler.create_badge.called)

    @patch('requests.get')
    def test_ensure_badge_created_creates(self, get):
        response = Mock()
        response.status_code = 404
        get.return_value = response
        self.assertNotIn('fc5519bfbeff40a53dc6d36a894f5c468c7020edc3858cb86046bc8740c9c1f0', BadgeHandler.badges)
        self.handler.create_badge = Mock()
        self.handler.ensure_badge_created('honor')
        self.assertTrue(self.handler.create_badge.called)
        self.assertEqual(self.handler.create_badge.call_args, call('honor'))
        self.assertTrue(BadgeHandler.badges['fc5519bfbeff40a53dc6d36a894f5c468c7020edc3858cb86046bc8740c9c1f0'])

    @patch('requests.post')
    def test_create_assertion(self, post):
        result = {'json': {'image': 'http://www.example.com/example.png'}}
        response = Mock()
        response.json.return_value = result
        post.return_value = response
        self.handler.create_assertion(self.user, 'honor')
        args, kwargs = post.call_args
        self.assertEqual(
            args[0],
            'https://example.com/v1/issuer/issuers/test-issuer/badges/'
            'fc5519bfbeff40a53dc6d36a894f5c468c7020edc3858cb86046bc8740c9c1f0/assertions'
        )
        self.check_headers(kwargs['headers'])
        self.assertEqual(kwargs['data'], {'email': 'example@example.com'})
        badge = BadgeAssertion.objects.get(user=self.user, course_id=self.course.location.course_key)
        self.assertEqual(badge.data, result)
        self.assertEqual(badge.image_url, 'http://www.example.com/example.png')
