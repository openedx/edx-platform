"""
Tests for the badges API views.
"""
from django.conf import settings
from django.test.utils import override_settings

from badges.tests.factories import BadgeAssertionFactory, BadgeClassFactory, RandomBadgeClassFactory
from openedx.core.lib.api.test_utils import ApiTestCase
from student.tests.factories import UserFactory
from util.testing import UrlResetMixin
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

FEATURES_WITH_BADGES_ENABLED = settings.FEATURES.copy()
FEATURES_WITH_BADGES_ENABLED['ENABLE_OPENBADGES'] = True


@override_settings(FEATURES=FEATURES_WITH_BADGES_ENABLED)
class UserAssertionTestCase(UrlResetMixin, ModuleStoreTestCase, ApiTestCase):
    """
    Mixin for badge API tests.
    """
    WILDCARD = False
    CHECK_COURSE = False

    def setUp(self, *args, **kwargs):
        super(UserAssertionTestCase, self).setUp(*args, **kwargs)
        self.course = CourseFactory.create()
        self.user = UserFactory.create()
        # Password defined by factory.
        self.client.login(username=self.user.username, password='test')

    def url(self):
        """
        Return the URL to look up the current user's assertions.
        """
        return '/api/badges/v1/assertions/user/{}/'.format(self.user.username)

    def check_class_structure(self, badge_class, json_class):
        """
        Check a JSON response against a known badge class.
        """
        self.assertEqual(badge_class.issuing_component, json_class['issuing_component'])
        self.assertEqual(badge_class.slug, json_class['slug'])
        self.assertIn(badge_class.image.url, json_class['image_url'])
        self.assertEqual(badge_class.description, json_class['description'])
        self.assertEqual(badge_class.criteria, json_class['criteria'])
        self.assertEqual(badge_class.course_id and unicode(badge_class.course_id), json_class['course_id'])

    def check_assertion_structure(self, assertion, json_assertion):
        """
        Check a JSON response against a known assertion object.
        """
        self.assertEqual(assertion.image_url, json_assertion['image_url'])
        self.assertEqual(assertion.assertion_url, json_assertion['assertion_url'])
        self.check_class_structure(assertion.badge_class, json_assertion['badge_class'])

    def get_course_id(self, badge_class):
        """
        Used for tests which may need to test for a course_id or a wildcard.
        """
        if self.WILDCARD:
            return '*'
        else:
            return unicode(badge_class.course_id)

    def create_badge_class(self, **kwargs):
        """
        Create a badge class, using a course id if it's relevant to the URL pattern.
        """
        if self.CHECK_COURSE:
            return RandomBadgeClassFactory.create(course_id=self.course.location.course_key, **kwargs)
        return RandomBadgeClassFactory.create(**kwargs)

    def get_qs_args(self, badge_class):
        """
        Get a dictionary to be serialized into querystring params based on class settings.
        """
        qs_args = {
            'issuing_component': badge_class.issuing_component,
            'slug': badge_class.slug,
        }
        if self.CHECK_COURSE:
            qs_args['course_id'] = self.get_course_id(badge_class)
        return qs_args


class TestUserBadgeAssertions(UserAssertionTestCase):
    """
    Test the general badge assertions retrieval view.
    """

    def test_get_assertions(self):
        """
        Verify we can get all of a user's badge assertions.
        """
        for dummy in range(3):
            BadgeAssertionFactory(user=self.user)
        # Add in a course scoped badge-- these should not be excluded from the full listing.
        BadgeAssertionFactory(user=self.user, badge_class=BadgeClassFactory(course_id=self.course.location.course_key))
        # Should not be included.
        for dummy in range(3):
            self.create_badge_class()
        response = self.get_json(self.url())
        # pylint: disable=no-member
        self.assertEqual(len(response['results']), 4)

    def test_assertion_structure(self):
        badge_class = self.create_badge_class()
        assertion = BadgeAssertionFactory.create(user=self.user, badge_class=badge_class)
        response = self.get_json(self.url())
        # pylint: disable=no-member
        self.check_assertion_structure(assertion, response['results'][0])


class TestUserCourseBadgeAssertions(UserAssertionTestCase):
    """
    Test the Badge Assertions view with the course_id filter.
    """
    CHECK_COURSE = True

    def test_get_assertions(self):
        """
        Verify we can get assertions via the course_id and username.
        """
        course_key = self.course.location.course_key
        badge_class = BadgeClassFactory.create(course_id=course_key)
        for dummy in range(3):
            BadgeAssertionFactory.create(user=self.user, badge_class=badge_class)
        # Should not be included.
        for dummy in range(3):
            BadgeAssertionFactory.create(user=self.user)
        # Also should not be included
        for dummy in range(6):
            BadgeAssertionFactory.create(badge_class=badge_class)
        response = self.get_json(self.url(), data={'course_id': course_key})
        # pylint: disable=no-member
        self.assertEqual(len(response['results']), 3)
        unused_course = CourseFactory.create()
        response = self.get_json(self.url(), data={'course_id': unused_course.location.course_key})
        # pylint: disable=no-member
        self.assertEqual(len(response['results']), 0)

    def test_assertion_structure(self):
        """
        Verify the badge assertion structure is not mangled in this mode.
        """
        course_key = self.course.location.course_key
        badge_class = BadgeClassFactory.create(course_id=course_key)
        assertion = BadgeAssertionFactory.create(badge_class=badge_class, user=self.user)
        response = self.get_json(self.url())
        # pylint: disable=no-member
        self.check_assertion_structure(assertion, response['results'][0])


class TestUserBadgeAssertionsByClass(UserAssertionTestCase):
    """
    Test the Badge Assertions view with the badge class filter.
    """

    def test_get_assertions(self):
        """
        Verify we can get assertions via the badge class and username.
        """
        badge_class = self.create_badge_class()
        for dummy in range(3):
            BadgeAssertionFactory.create(user=self.user, badge_class=badge_class)
        if badge_class.course_id:
            # Also create a version of this badge under a different course.
            alt_class = BadgeClassFactory.create(
                slug=badge_class.slug, issuing_component=badge_class.issuing_component,
                course_id=CourseFactory.create().location.course_key
            )
            BadgeAssertionFactory.create(user=self.user, badge_class=alt_class)
        # Should not be in list.
        for dummy in range(5):
            BadgeAssertionFactory.create(badge_class=badge_class)
        # Also should not be in list.
        for dummy in range(6):
            BadgeAssertionFactory.create()

        response = self.get_json(
            self.url(),
            data=self.get_qs_args(badge_class),
        )
        if self.WILDCARD:
            expected_length = 4
        else:
            expected_length = 3
        # pylint: disable=no-member
        self.assertEqual(len(response['results']), expected_length)
        unused_class = self.create_badge_class(slug='unused_slug', issuing_component='unused_component')

        response = self.get_json(
            self.url(),
            data=self.get_qs_args(unused_class),
        )
        # pylint: disable=no-member
        self.assertEqual(len(response['results']), 0)

    def check_badge_class_assertion(self, badge_class):
        """
        Given a badge class, create an assertion for the current user and fetch it, checking the structure.
        """
        assertion = BadgeAssertionFactory.create(badge_class=badge_class, user=self.user)
        response = self.get_json(
            self.url(),
            data=self.get_qs_args(badge_class),
        )
        # pylint: disable=no-member
        self.check_assertion_structure(assertion, response['results'][0])

    def test_assertion_structure(self):
        self.check_badge_class_assertion(self.create_badge_class())

    def test_empty_issuing_component(self):
        self.check_badge_class_assertion(self.create_badge_class(issuing_component=''))


# pylint: disable=test-inherits-tests
class TestUserBadgeAssertionsByClassCourse(TestUserBadgeAssertionsByClass):
    """
    Test searching all assertions for a user with a course bound badge class.
    """
    CHECK_COURSE = True


# pylint: disable=test-inherits-tests
class TestUserBadgeAssertionsByClassWildCard(TestUserBadgeAssertionsByClassCourse):
    """
    Test searching slugs/issuing_components across all course IDs.
    """
    WILDCARD = True
