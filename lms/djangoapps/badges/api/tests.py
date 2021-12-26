"""
Tests for the badges API views.
"""


from ddt import data, ddt, unpack
from django.conf import settings
from django.test.utils import override_settings

from common.djangoapps.student.tests.factories import UserFactory
from common.djangoapps.util.testing import UrlResetMixin
from lms.djangoapps.badges.tests.factories import BadgeAssertionFactory, BadgeClassFactory, RandomBadgeClassFactory
from openedx.core.lib.api.test_utils import ApiTestCase
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.tests.factories import CourseFactory  # lint-amnesty, pylint: disable=wrong-import-order

FEATURES_WITH_BADGES_ENABLED = settings.FEATURES.copy()
FEATURES_WITH_BADGES_ENABLED['ENABLE_OPENBADGES'] = True


@override_settings(FEATURES=FEATURES_WITH_BADGES_ENABLED)
class UserAssertionTestCase(UrlResetMixin, ModuleStoreTestCase, ApiTestCase):
    """
    Mixin for badge API tests.
    """

    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create()
        self.user = UserFactory.create()
        # Password defined by factory.
        self.client.login(username=self.user.username, password='test')

    def url(self):
        """
        Return the URL to look up the current user's assertions.
        """
        return f'/api/badges/v1/assertions/user/{self.user.username}/'

    def check_class_structure(self, badge_class, json_class):
        """
        Check a JSON response against a known badge class.
        """
        assert badge_class.issuing_component == json_class['issuing_component']
        assert badge_class.slug == json_class['slug']
        assert badge_class.image.url in json_class['image_url']
        assert badge_class.description == json_class['description']
        assert badge_class.criteria == json_class['criteria']
        assert (badge_class.course_id and str(badge_class.course_id)) == json_class['course_id']

    def check_assertion_structure(self, assertion, json_assertion):
        """
        Check a JSON response against a known assertion object.
        """
        assert assertion.image_url == json_assertion['image_url']
        assert assertion.assertion_url == json_assertion['assertion_url']
        self.check_class_structure(assertion.badge_class, json_assertion['badge_class'])

    def get_course_id(self, wildcard, badge_class):
        """
        Used for tests which may need to test for a course_id or a wildcard.
        """
        if wildcard:
            return '*'
        else:
            return str(badge_class.course_id)

    def create_badge_class(self, check_course, **kwargs):
        """
        Create a badge class, using a course id if it's relevant to the URL pattern.
        """
        if check_course:
            return RandomBadgeClassFactory.create(course_id=self.course.location.course_key, **kwargs)
        return RandomBadgeClassFactory.create(**kwargs)

    def get_qs_args(self, check_course, wildcard, badge_class):
        """
        Get a dictionary to be serialized into querystring params based on class settings.
        """
        qs_args = {
            'issuing_component': badge_class.issuing_component,
            'slug': badge_class.slug,
        }
        if check_course:
            qs_args['course_id'] = self.get_course_id(wildcard, badge_class)
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
            self.create_badge_class(False)
        response = self.get_json(self.url())
        assert len(response['results']) == 4

    def test_assertion_structure(self):
        badge_class = self.create_badge_class(False)
        assertion = BadgeAssertionFactory.create(user=self.user, badge_class=badge_class)
        response = self.get_json(self.url())
        self.check_assertion_structure(assertion, response['results'][0])


class TestUserCourseBadgeAssertions(UserAssertionTestCase):
    """
    Test the Badge Assertions view with the course_id filter.
    """

    def test_get_assertions(self):
        """
        Verify we can get assertions via the course_id and username.
        """
        course_key = self.course.location.course_key
        badge_class = BadgeClassFactory.create(course_id=course_key)
        for dummy in range(3):
            BadgeAssertionFactory.create(user=self.user, badge_class=badge_class)
        # Should not be included, as they don't share the target badge class.
        for dummy in range(3):
            BadgeAssertionFactory.create(user=self.user)
        # Also should not be included, as they don't share the same user.
        for dummy in range(6):
            BadgeAssertionFactory.create(badge_class=badge_class)
        response = self.get_json(self.url(), data={'course_id': str(course_key)})
        assert len(response['results']) == 3
        unused_course = CourseFactory.create()
        response = self.get_json(self.url(), data={'course_id': str(unused_course.location.course_key)})
        assert len(response['results']) == 0

    def test_assertion_structure(self):
        """
        Verify the badge assertion structure is as expected when a course is involved.
        """
        course_key = self.course.location.course_key
        badge_class = BadgeClassFactory.create(course_id=course_key)
        assertion = BadgeAssertionFactory.create(badge_class=badge_class, user=self.user)
        response = self.get_json(self.url())
        self.check_assertion_structure(assertion, response['results'][0])


@ddt
class TestUserBadgeAssertionsByClass(UserAssertionTestCase):
    """
    Test the Badge Assertions view with the badge class filter.
    """

    @unpack
    @data((False, False), (True, False), (True, True))
    def test_get_assertions(self, check_course, wildcard):
        """
        Verify we can get assertions via the badge class and username.
        """
        badge_class = self.create_badge_class(check_course)
        for dummy in range(3):
            BadgeAssertionFactory.create(user=self.user, badge_class=badge_class)
        if badge_class.course_id:
            # Also create a version of this badge under a different course.
            alt_class = BadgeClassFactory.create(
                slug=badge_class.slug, issuing_component=badge_class.issuing_component,
                course_id=CourseFactory.create().location.course_key
            )
            BadgeAssertionFactory.create(user=self.user, badge_class=alt_class)
        # Same badge class, but different user. Should not show up in the list.
        for dummy in range(5):
            BadgeAssertionFactory.create(badge_class=badge_class)
        # Different badge class AND different user. Certainly shouldn't show up in the list!
        for dummy in range(6):
            BadgeAssertionFactory.create()

        response = self.get_json(
            self.url(),
            data=self.get_qs_args(check_course, wildcard, badge_class),
        )
        if wildcard:
            expected_length = 4
        else:
            expected_length = 3
        assert len(response['results']) == expected_length
        unused_class = self.create_badge_class(check_course, slug='unused_slug', issuing_component='unused_component')

        response = self.get_json(
            self.url(),
            data=self.get_qs_args(check_course, wildcard, unused_class),
        )
        assert len(response['results']) == 0

    def check_badge_class_assertion(self, check_course, wildcard, badge_class):
        """
        Given a badge class, create an assertion for the current user and fetch it, checking the structure.
        """
        assertion = BadgeAssertionFactory.create(badge_class=badge_class, user=self.user)
        response = self.get_json(
            self.url(),
            data=self.get_qs_args(check_course, wildcard, badge_class),
        )
        self.check_assertion_structure(assertion, response['results'][0])

    @unpack
    @data((False, False), (True, False), (True, True))
    def test_assertion_structure(self, check_course, wildcard):
        self.check_badge_class_assertion(check_course, wildcard, self.create_badge_class(check_course))

    @unpack
    @data((False, False), (True, False), (True, True))
    def test_empty_issuing_component(self, check_course, wildcard):
        self.check_badge_class_assertion(
            check_course, wildcard, self.create_badge_class(check_course, issuing_component='')
        )
