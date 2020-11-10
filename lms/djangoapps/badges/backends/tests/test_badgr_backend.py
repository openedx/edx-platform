"""
Tests for BadgrBackend
"""


from datetime import datetime

import ddt
import six
from django.db.models.fields.files import ImageFieldFile
from django.test.utils import override_settings
from lazy.lazy import lazy
from mock import Mock, call, patch

from lms.djangoapps.badges.backends.badgr import BadgrBackend
from lms.djangoapps.badges.models import BadgeAssertion
from lms.djangoapps.badges.tests.factories import BadgeClassFactory
from openedx.core.lib.tests.assertions.events import assert_event_matches
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from common.djangoapps.track.tests import EventTrackingTestCase
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

BADGR_SETTINGS = {
    'BADGR_API_TOKEN': '12345',
    'BADGR_BASE_URL': 'https://example.com',
    'BADGR_ISSUER_SLUG': 'test-issuer',
}

# Should be the hashed result of test_slug as the slug, and test_component as the component
EXAMPLE_SLUG = '15bb687e0c59ef2f0a49f6838f511bf4ca6c566dd45da6293cabbd9369390e1a'


# pylint: disable=protected-access
@ddt.ddt
@override_settings(**BADGR_SETTINGS)
class BadgrBackendTestCase(ModuleStoreTestCase, EventTrackingTestCase):
    """
    Tests the BadgeHandler object
    """

    def setUp(self):
        """
        Create a course and user to test with.
        """
        super(BadgrBackendTestCase, self).setUp()
        # Need key to be deterministic to test slugs.
        self.course = CourseFactory.create(
            org='edX', course='course_test', run='test_run', display_name='Badged',
            start=datetime(year=2015, month=5, day=19),
            end=datetime(year=2015, month=5, day=20)
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

    @lazy
    def handler(self):
        """
        Lazily loads a BadgeHandler object for the current course. Can't do this on setUp because the settings
        overrides aren't in place.
        """
        return BadgrBackend()

    def test_urls(self):
        """
        Make sure the handler generates the correct URLs for different API tasks.
        """
        self.assertEqual(self.handler._base_url, 'https://example.com/v1/issuer/issuers/test-issuer')
        self.assertEqual(self.handler._badge_create_url, 'https://example.com/v1/issuer/issuers/test-issuer/badges')
        self.assertEqual(
            self.handler._badge_url('test_slug_here'),
            'https://example.com/v1/issuer/issuers/test-issuer/badges/test_slug_here'
        )
        self.assertEqual(
            self.handler._assertion_url('another_test_slug'),
            'https://example.com/v1/issuer/issuers/test-issuer/badges/another_test_slug/assertions'
        )

    def check_headers(self, headers):
        """
        Verify the a headers dict from a requests call matches the proper auth info.
        """
        self.assertEqual(headers, {'Authorization': 'Token 12345'})

    def test_get_headers(self):
        """
        Check to make sure the handler generates appropriate HTTP headers.
        """
        self.check_headers(self.handler._get_headers())

    @patch('requests.post')
    def test_create_badge(self, post):
        """
        Verify badge spec creation works.
        """
        self.handler._create_badge(self.badge_class)
        args, kwargs = post.call_args
        self.assertEqual(args[0], 'https://example.com/v1/issuer/issuers/test-issuer/badges')
        self.assertEqual(kwargs['files']['image'][0], self.badge_class.image.name)
        self.assertIsInstance(kwargs['files']['image'][1], ImageFieldFile)
        self.assertEqual(kwargs['files']['image'][2], 'image/png')
        self.check_headers(kwargs['headers'])
        self.assertEqual(
            kwargs['data'],
            {
                'name': 'Test Badge',
                'slug': EXAMPLE_SLUG,
                'criteria': 'https://example.com/syllabus',
                'description': "Yay! It's a test badge.",
            }
        )

    def test_ensure_badge_created_cache(self):
        """
        Make sure ensure_badge_created doesn't call create_badge if we know the badge is already there.
        """
        BadgrBackend.badges.append(EXAMPLE_SLUG)
        self.handler._create_badge = Mock()
        self.handler._ensure_badge_created(self.badge_class)
        self.assertFalse(self.handler._create_badge.called)

    @ddt.unpack
    @ddt.data(
        ('badge_class', EXAMPLE_SLUG),
        ('legacy_badge_class', 'test_slug'),
        ('no_course_badge_class', 'test_componenttest_slug')
    )
    def test_slugs(self, badge_class_type, slug):
        self.assertEqual(self.handler._slugify(getattr(self, badge_class_type)), slug)

    @patch('requests.get')
    def test_ensure_badge_created_checks(self, get):
        response = Mock()
        response.status_code = 200
        get.return_value = response
        self.assertNotIn('test_componenttest_slug', BadgrBackend.badges)
        self.handler._create_badge = Mock()
        self.handler._ensure_badge_created(self.badge_class)
        self.assertTrue(get.called)
        args, kwargs = get.call_args
        self.assertEqual(
            args[0],
            'https://example.com/v1/issuer/issuers/test-issuer/badges/' +
            EXAMPLE_SLUG
        )
        self.check_headers(kwargs['headers'])
        self.assertIn(EXAMPLE_SLUG, BadgrBackend.badges)
        self.assertFalse(self.handler._create_badge.called)

    @patch('requests.get')
    def test_ensure_badge_created_creates(self, get):
        response = Mock()
        response.status_code = 404
        get.return_value = response
        self.assertNotIn(EXAMPLE_SLUG, BadgrBackend.badges)
        self.handler._create_badge = Mock()
        self.handler._ensure_badge_created(self.badge_class)
        self.assertTrue(self.handler._create_badge.called)
        self.assertEqual(self.handler._create_badge.call_args, call(self.badge_class))
        self.assertIn(EXAMPLE_SLUG, BadgrBackend.badges)

    @patch('requests.post')
    def test_badge_creation_event(self, post):
        result = {
            'json': {'id': 'http://www.example.com/example'},
            'image': 'http://www.example.com/example.png',
            'badge': 'test_assertion_slug',
            'issuer': 'https://example.com/v1/issuer/issuers/test-issuer',
        }
        response = Mock()
        response.json.return_value = result
        post.return_value = response
        self.recreate_tracker()
        self.handler._create_assertion(self.badge_class, self.user, 'https://example.com/irrefutable_proof')
        args, kwargs = post.call_args
        self.assertEqual(
            args[0],
            'https://example.com/v1/issuer/issuers/test-issuer/badges/' +
            EXAMPLE_SLUG +
            '/assertions'
        )
        self.check_headers(kwargs['headers'])
        assertion = BadgeAssertion.objects.get(user=self.user, badge_class__course_id=self.course.location.course_key)
        self.assertEqual(assertion.data, result)
        self.assertEqual(assertion.image_url, 'http://www.example.com/example.png')
        self.assertEqual(assertion.assertion_url, 'http://www.example.com/example')
        self.assertEqual(kwargs['data'], {
            'email': 'example@example.com',
            'evidence': 'https://example.com/irrefutable_proof'
        })
        assert_event_matches({
            'name': 'edx.badge.assertion.created',
            'data': {
                'user_id': self.user.id,
                'course_id': six.text_type(self.course.location.course_key),
                'enrollment_mode': 'honor',
                'assertion_id': assertion.id,
                'badge_name': 'Test Badge',
                'badge_slug': 'test_slug',
                'issuing_component': 'test_component',
                'assertion_image_url': 'http://www.example.com/example.png',
                'assertion_json_url': 'http://www.example.com/example',
                'issuer': 'https://example.com/v1/issuer/issuers/test-issuer',
            }
        }, self.get_event())
