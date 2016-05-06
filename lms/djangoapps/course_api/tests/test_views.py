"""
Tests for Course API views.
"""
from hashlib import md5

from django.core.urlresolvers import reverse
from django.test import RequestFactory
from nose.plugins.attrib import attr

from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase, ModuleStoreTestCase
from .mixins import CourseApiFactoryMixin, TEST_PASSWORD
from ..views import CourseDetailView


class CourseApiTestViewMixin(CourseApiFactoryMixin):
    """
    Mixin class for test helpers for Course API views
    """

    def setup_user(self, requesting_user, make_inactive=False):
        """
        log in the specified user and set its is_active field
        """
        self.assertTrue(self.client.login(username=requesting_user.username, password=TEST_PASSWORD))
        if make_inactive:
            requesting_user.is_active = False
            requesting_user.save()

    def verify_response(self, expected_status_code=200, params=None, url=None):
        """
        Ensure that sending a GET request to self.url returns the expected
        status code (200 by default).

        Arguments:
            expected_status_code: (default 200)
            params:
                query parameters to include in the request. Can include
                `username`.

        Returns:
            response: (HttpResponse) The response returned by the request
        """
        query_params = {}
        query_params.update(params or {})
        response = self.client.get(url or self.url, data=query_params)
        self.assertEqual(response.status_code, expected_status_code)
        return response


@attr('shard_3')
class CourseListViewTestCase(CourseApiTestViewMixin, SharedModuleStoreTestCase):
    """
    Test responses returned from CourseListView.
    """

    @classmethod
    def setUpClass(cls):
        super(CourseListViewTestCase, cls).setUpClass()
        cls.course = cls.create_course()
        cls.url = reverse('course-list')
        cls.staff_user = cls.create_user(username='staff', is_staff=True)
        cls.honor_user = cls.create_user(username='honor', is_staff=False)

    def test_as_staff(self):
        self.setup_user(self.staff_user)
        self.verify_response(params={'username': self.staff_user.username})

    def test_as_staff_for_honor(self):
        self.setup_user(self.staff_user)
        self.verify_response(params={'username': self.honor_user.username})

    def test_as_honor(self):
        self.setup_user(self.honor_user)
        self.verify_response(params={'username': self.honor_user.username})

    def test_as_honor_for_explicit_self(self):
        self.setup_user(self.honor_user)
        self.verify_response(params={'username': self.honor_user.username})

    def test_as_honor_for_staff(self):
        self.setup_user(self.honor_user)
        self.verify_response(expected_status_code=403, params={'username': self.staff_user.username})

    def test_as_inactive_user(self):
        inactive_user = self.create_user(username='inactive', is_staff=False)
        self.setup_user(inactive_user, make_inactive=True)
        self.verify_response(params={'username': inactive_user.username})

    def test_missing_username(self):
        self.setup_user(self.honor_user)
        response_to_missing_username = self.verify_response(expected_status_code=200)
        self.assertIsNotNone(response_to_missing_username.data)  # pylint: disable=no-member

    def test_not_logged_in(self):
        self.client.logout()
        self.verify_response()


class CourseListViewTestCaseMultipleCourses(CourseApiTestViewMixin, ModuleStoreTestCase):
    """
    Test responses returned from CourseListView (with tests that modify the
    courseware).
    """

    def setUp(self):
        super(CourseListViewTestCaseMultipleCourses, self).setUp()
        self.course = self.create_course()
        self.url = reverse('course-list')
        self.staff_user = self.create_user(username='staff', is_staff=True)
        self.honor_user = self.create_user(username='honor', is_staff=False)

    def test_filter_by_org(self):
        """Verify that CourseOverviews are filtered by the provided org key."""
        self.setup_user(self.staff_user)

        # Create a second course to be filtered out of queries.
        alternate_course = self.create_course(
            org=md5(self.course.org).hexdigest()
        )

        self.assertNotEqual(alternate_course.org, self.course.org)

        # No filtering.
        unfiltered_response = self.verify_response(params={'username': self.staff_user.username})
        for org in [self.course.org, alternate_course.org]:
            self.assertTrue(
                any(course['org'] == org for course in unfiltered_response.data['results'])  # pylint: disable=no-member
            )

        # With filtering.
        filtered_response = self.verify_response(params={'org': self.course.org, 'username': self.staff_user.username})
        self.assertTrue(
            all(course['org'] == self.course.org for course in filtered_response.data['results'])  # pylint: disable=no-member
        )

    def test_filter(self):
        self.setup_user(self.staff_user)

        # Create a second course to be filtered out of queries.
        alternate_course = self.create_course(course='mobile', mobile_available=True)

        test_cases = [
            (None, [alternate_course, self.course]),
            (dict(mobile=True), [alternate_course]),
            (dict(mobile=False), [self.course]),
        ]
        for filter_, expected_courses in test_cases:
            params = {'username': self.staff_user.username}
            if filter_:
                params.update(filter_)
            response = self.verify_response(params=params)
            self.assertEquals(
                {course['course_id'] for course in response.data['results']},  # pylint: disable=no-member
                {unicode(course.id) for course in expected_courses},
                "testing course_api.views.CourseListView with filter_={}".format(filter_),
            )


class CourseDetailViewTestCase(CourseApiTestViewMixin, SharedModuleStoreTestCase):
    """
    Test responses returned from CourseDetailView.
    """

    @classmethod
    def setUpClass(cls):
        super(CourseDetailViewTestCase, cls).setUpClass()
        cls.course = cls.create_course()
        cls.hidden_course = cls.create_course(course=u'hidden', visible_to_staff_only=True)
        cls.url = reverse('course-detail', kwargs={'course_key_string': cls.course.id})
        cls.hidden_url = reverse('course-detail', kwargs={'course_key_string': cls.hidden_course.id})
        cls.nonexistent_url = reverse('course-detail', kwargs={'course_key_string': 'edX/nope/Fall_2014'})
        cls.staff_user = cls.create_user(username='staff', is_staff=True)
        cls.honor_user = cls.create_user(username='honor', is_staff=False)

    def test_as_honor(self):
        self.setup_user(self.honor_user)
        self.verify_response(params={'username': self.honor_user.username})

    def test_as_honor_for_staff(self):
        self.setup_user(self.honor_user)
        self.verify_response(expected_status_code=403, params={'username': self.staff_user.username})

    def test_as_staff(self):
        self.setup_user(self.staff_user)
        self.verify_response(params={'username': self.staff_user.username})

    def test_as_staff_for_honor(self):
        self.setup_user(self.staff_user)
        self.verify_response(params={'username': self.honor_user.username})

    def test_as_anonymous_user(self):
        self.verify_response(expected_status_code=200)

    def test_as_inactive_user(self):
        inactive_user = self.create_user(username='inactive', is_staff=False)
        self.setup_user(inactive_user, make_inactive=True)
        self.verify_response(params={'username': inactive_user.username})

    def test_hidden_course_as_honor(self):
        self.setup_user(self.honor_user)
        self.verify_response(
            expected_status_code=404, url=self.hidden_url, params={'username': self.honor_user.username}
        )

    def test_hidden_course_as_staff(self):
        self.setup_user(self.staff_user)
        self.verify_response(url=self.hidden_url, params={'username': self.staff_user.username})

    def test_nonexistent_course(self):
        self.setup_user(self.staff_user)
        self.verify_response(
            expected_status_code=404, url=self.nonexistent_url, params={'username': self.staff_user.username}
        )

    def test_invalid_course_key(self):
        # Our URL patterns try to block invalid course keys.  If one got
        # through, this is how the view would respond.
        request_factory = RequestFactory()
        request = request_factory.get('/')
        request.query_params = {}
        request.user = self.staff_user
        response = CourseDetailView().dispatch(request, course_key_string='a:b:c')
        self.assertEquals(response.status_code, 400)
