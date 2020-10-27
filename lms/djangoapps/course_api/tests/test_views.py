"""
Tests for Course API views.
"""
import ddt
from hashlib import md5

from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.test import RequestFactory
from django.test.utils import override_settings
from search.tests.test_course_discovery import DemoCourse
from search.tests.tests import TEST_INDEX_NAME
from search.tests.utils import SearcherMixin

from openedx.core.lib.tests import attr
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, SharedModuleStoreTestCase
from waffle.testutils import override_switch

from ..views import CourseDetailView, CourseListUserThrottle
from .mixins import TEST_PASSWORD, CourseApiFactoryMixin


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


@attr(shard=9)
@ddt.ddt
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
        self.assertIsNotNone(response_to_missing_username.data)

    def test_not_logged_in(self):
        self.client.logout()
        self.verify_response()

    def assert_throttle_configured_correctly(self, user_scope, throws_exception, expected_rate):
        """Helper to determine throttle configuration is correctly set."""
        throttle = CourseListUserThrottle()
        throttle.check_for_switches()
        throttle.scope = user_scope
        try:
            rate_limit, __ = throttle.parse_rate(throttle.get_rate())
            self.assertEqual(rate_limit, expected_rate)
            self.assertFalse(throws_exception)
        except ImproperlyConfigured:
            self.assertTrue(throws_exception)

    @ddt.data(('staff', False, 40), ('user', False, 20), ('unknown', True, None))
    @ddt.unpack
    def test_throttle_rate_default(self, user_scope, throws_exception, expected_rate):
        """ Make sure throttle rate default is set correctly for different user scopes. """
        self.assert_throttle_configured_correctly(user_scope, throws_exception, expected_rate)

    @ddt.data(('staff', False, 10), ('user', False, 2), ('unknown', True, None))
    @ddt.unpack
    @override_switch('course_list_api_rate_limit.rate_limit_2', active=True)
    def test_throttle_rate_2(self, user_scope, throws_exception, expected_rate):
        """ Make sure throttle rate 2 is set correctly for different user scopes. """
        self.assert_throttle_configured_correctly(user_scope, throws_exception, expected_rate)

    @ddt.data(('staff', False, 20), ('user', False, 10), ('unknown', True, None))
    @ddt.unpack
    @override_switch('course_list_api_rate_limit.rate_limit_10', active=True)
    def test_throttle_rate_20(self, user_scope, throws_exception, expected_rate):
        """ Make sure throttle rate 20 is set correctly for different user scopes. """
        self.assert_throttle_configured_correctly(user_scope, throws_exception, expected_rate)


@attr(shard=9)
class CourseListViewTestCaseMultipleCourses(CourseApiTestViewMixin, ModuleStoreTestCase):
    """
    Test responses returned from CourseListView (with tests that modify the
    courseware).
    """
    ENABLED_SIGNALS = ['course_published']

    def setUp(self):
        super(CourseListViewTestCaseMultipleCourses, self).setUp()
        self.course = self.create_course(mobile_available=False)
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
                any(course['org'] == org for course in unfiltered_response.data['results'])
            )

        # With filtering.
        filtered_response = self.verify_response(params={'org': self.course.org, 'username': self.staff_user.username})
        self.assertTrue(
            all(course['org'] == self.course.org for course in filtered_response.data['results'])
        )

    def test_filter(self):
        self.setup_user(self.staff_user)

        # Create a second course to be filtered out of queries.
        alternate_course = self.create_course(course='mobile')

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
                {course['course_id'] for course in response.data['results']},
                {unicode(course.id) for course in expected_courses},
                "testing course_api.views.CourseListView with filter_={}".format(filter_),
            )


@attr(shard=9)
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


@attr(shard=9)
@override_settings(ELASTIC_FIELD_MAPPINGS={
    'start_date': {'type': 'date'},
    'enrollment_start': {'type': 'date'},
    'enrollment_end': {'type': 'date'}
})
@override_settings(SEARCH_ENGINE="search.tests.mock_search_engine.MockSearchEngine")
@override_settings(COURSEWARE_INDEX_NAME=TEST_INDEX_NAME)
class CourseListSearchViewTest(CourseApiTestViewMixin, ModuleStoreTestCase, SearcherMixin):
    """
    Tests the search functionality of the courses API.

    Similar to search.tests.test_course_discovery_views but with the course API integration.
    """

    ENABLED_SIGNALS = ['course_published']

    def setUp(self):
        super(CourseListSearchViewTest, self).setUp()
        DemoCourse.reset_count()
        self.searcher.destroy()

        self.courses = [
            self.create_and_index_course('OrgA', 'Find this one with the right parameter'),
            self.create_and_index_course('OrgB', 'Find this one with another parameter'),
            self.create_and_index_course('OrgC', 'This course has a unique search term'),
        ]

        self.url = reverse('course-list')
        self.staff_user = self.create_user(username='staff', is_staff=True)
        self.honor_user = self.create_user(username='honor', is_staff=False)

    def create_and_index_course(self, org_code, short_description):
        """
        Add a course to both database and search.

        Warning: A ton of gluing here! If this fails, double check both CourseListViewTestCase and MockSearchUrlTest.
        """

        search_course = DemoCourse.get({
            'org': org_code,
            'run': '2010',
            'number': 'DemoZ',
            # Using the slash separated course ID bcuz `DemoCourse` isn't updated yet to new locator.
            'id': '{org_code}/DemoZ/2010'.format(org_code=org_code),
            'content': {
                'short_description': short_description,
            },
        })

        DemoCourse.index(self.searcher, [search_course])

        org, course, run = search_course['id'].split('/')

        db_course = self.create_course(
            mobile_available=False,
            org=org,
            course=course,
            run=run,
            short_description=short_description,
        )

        return db_course

    def test_list_all(self):
        """
        Test without search, should list all the courses.
        """
        res = self.verify_response()
        self.assertIn('results', res.data)
        self.assertNotEqual(res.data['results'], [])
        self.assertEqual(res.data['pagination']['count'], 3)  # Should list all of the 3 courses

    def test_list_all_with_search_term(self):
        """
        Test with search, should only the course that matches the search term.
        """
        res = self.verify_response(params={'search_term': 'unique search term'})
        self.assertIn('results', res.data)
        self.assertNotEqual(res.data['results'], [])
        self.assertEqual(res.data['pagination']['count'], 1)  # Should list a single course
