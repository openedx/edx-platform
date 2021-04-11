"""
Tests for Course API views.
"""


from datetime import datetime
from hashlib import md5
from unittest import TestCase

import ddt
import six
from six.moves import range
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory
from django.test.utils import override_settings
from django.urls import reverse
from edx_django_utils.cache import RequestCache
from search.tests.test_course_discovery import DemoCourse
from search.tests.tests import TEST_INDEX_NAME
from search.tests.utils import SearcherMixin
from waffle.testutils import override_switch

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from opaque_keys.edx.locator import LibraryLocator
from openedx.core.lib.api.view_utils import LazySequence
from openedx.features.content_type_gating.models import ContentTypeGatingConfig
from openedx.features.course_duration_limits.models import CourseDurationLimitConfig
from common.djangoapps.student.auth import add_users
from common.djangoapps.student.roles import CourseInstructorRole, CourseStaffRole
from common.djangoapps.student.tests.factories import AdminFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from ..views import CourseDetailView, CourseListUserThrottle, LazyPageNumberPagination
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
            org=md5(self.course.org.encode('utf-8')).hexdigest()
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
            self.assertEqual(
                {course['course_id'] for course in response.data['results']},
                {six.text_type(course.id) for course in expected_courses},
                u"testing course_api.views.CourseListView with filter_={}".format(filter_),
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
        self.assertEqual(response.status_code, 400)


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
    ENABLED_CACHES = ModuleStoreTestCase.ENABLED_CACHES + ['configuration']

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
        self.audit_user = self.create_user(username='audit', is_staff=False)

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
        Test with search, should list only the course that matches the search term.
        """
        res = self.verify_response(params={'search_term': 'unique search term'})
        self.assertIn('results', res.data)
        self.assertNotEqual(res.data['results'], [])
        self.assertEqual(res.data['pagination']['count'], 1)
        self.assertEqual(len(res.data['results']), 1)  # Should return a single course

    def test_too_many_courses(self):
        """
        Test that search results are limited to 100 courses, and that they don't
        blow up the database.
        """

        ContentTypeGatingConfig.objects.create(
            enabled=True,
            enabled_as_of=datetime(2018, 1, 1),
        )

        CourseDurationLimitConfig.objects.create(
            enabled=True,
            enabled_as_of=datetime(2018, 1, 1),
        )

        course_ids = []

        # Create 300 courses across 30 organizations
        for org_num in range(10):
            org_id = 'org{}'.format(org_num)
            for course_num in range(30):
                course_name = 'course{}.{}'.format(org_num, course_num)
                course_run_name = 'run{}.{}'.format(org_num, course_num)
                course = CourseFactory.create(org=org_id, number=course_name, run=course_run_name, emit_signals=True)
                CourseModeFactory.create(course_id=course.id, mode_slug=CourseMode.AUDIT)
                CourseModeFactory.create(course_id=course.id, mode_slug=CourseMode.VERIFIED)
                course_ids.append(course.id)

        self.setup_user(self.audit_user)

        # These query counts were found empirically
        query_counts = [54, 46, 46, 46, 46, 46, 46, 46, 46, 46, 16]
        ordered_course_ids = sorted([str(cid) for cid in (course_ids + [c.id for c in self.courses])])

        self.clear_caches()

        for page in range(1, 12):
            RequestCache.clear_all_namespaces()
            with self.assertNumQueries(query_counts[page - 1]):
                response = self.verify_response(params={'page': page, 'page_size': 30})

                self.assertIn('results', response.data)
                self.assertEqual(response.data['pagination']['count'], 303)
                self.assertEqual(len(response.data['results']), 30 if page < 11 else 3)
                self.assertEqual(
                    [c['id'] for c in response.data['results']],
                    ordered_course_ids[(page - 1) * 30:page * 30]
                )


class CourseIdListViewTestCase(CourseApiTestViewMixin, ModuleStoreTestCase):
    """
    Test responses returned from CourseIdListView (with tests that modify the courseware).
    """
    ENABLED_SIGNALS = ['course_published']

    def setUp(self):
        super(CourseIdListViewTestCase, self).setUp()
        self.course = self.create_course()
        self.url = reverse('course-id-list')
        self.staff_user = self.create_user(username='staff', is_staff=True)
        self.honor_user = self.create_user(username='honor', is_staff=False)
        self.global_admin = AdminFactory()

    def test_filter_by_roles_global_staff(self):
        """
        Verify that global staff are always returned all courses irregardless of role filter.
        """
        self.setup_user(self.staff_user)

        # Request the courses as the staff user with the different roles specified.
        for role in ('staff', 'instructor'):
            filtered_response = self.verify_response(params={'username': self.staff_user.username, 'role': role})
            self.assertEqual(len(filtered_response.data['results']), 1)

    def test_filter_by_roles_non_staff(self):
        """
        Verify that a non-staff user can't access course_ids by role.
        """
        self.setup_user(self.honor_user)

        # Request the courses as the non-staff user with the different roles should *not* be allowed.
        for role in ('staff', 'instructor'):
            filtered_response = self.verify_response(params={'username': self.honor_user.username, 'role': role})
            self.assertEqual(len(filtered_response.data['results']), 0)

    def test_filter_by_roles_course_staff(self):
        """
        Verify that course_ids are filtered by the provided roles.
        """
        # Make this user a course staff user for the course.
        course_staff_user = self.create_user(username='course_staff', is_staff=False)
        add_users(self.global_admin, CourseStaffRole(self.course.id), course_staff_user)

        # Create a second course, along with an instructor user for it.
        alternate_course1 = self.create_course(org='test1')
        course_instructor_user = self.create_user(username='course_instructor', is_staff=False)
        add_users(self.global_admin, CourseInstructorRole(alternate_course1.id), course_instructor_user)

        # Create a third course, along with an user that has both staff and instructor for it.
        alternate_course2 = self.create_course(org='test2')
        course_instructor_staff_user = self.create_user(username='course_instructor_staff', is_staff=False)
        add_users(self.global_admin, CourseInstructorRole(alternate_course2.id), course_instructor_staff_user)
        add_users(self.global_admin, CourseStaffRole(alternate_course2.id), course_instructor_staff_user)

        # Requesting the courses for which the course staff user is staff should return *only* the single course.
        self.setup_user(self.staff_user)
        filtered_response = self.verify_response(params={
            'username': course_staff_user.username,
            'role': 'staff'
        })
        self.assertEqual(len(filtered_response.data['results']), 1)
        self.assertTrue(filtered_response.data['results'][0].startswith(self.course.org))

        # The course staff user does *not* have the course instructor role on any courses.
        filtered_response = self.verify_response(params={
            'username': course_staff_user.username,
            'role': 'instructor'
        })
        self.assertEqual(len(filtered_response.data['results']), 0)

        # The course instructor user only has the course instructor role on one course.
        filtered_response = self.verify_response(params={
            'username': course_instructor_user.username,
            'role': 'instructor'
        })
        self.assertEqual(len(filtered_response.data['results']), 1)
        self.assertTrue(filtered_response.data['results'][0].startswith(alternate_course1.org))

        # The course instructor user has the inferred course staff role on one course.
        self.setup_user(course_instructor_user)
        filtered_response = self.verify_response(params={
            'username': course_instructor_user.username,
            'role': 'staff'
        })
        self.assertEqual(len(filtered_response.data['results']), 1)
        self.assertTrue(filtered_response.data['results'][0].startswith(alternate_course1.org))

        # The user with both instructor AND staff on a course has the inferred course staff role on that one course.
        self.setup_user(course_instructor_staff_user)
        filtered_response = self.verify_response(params={
            'username': course_instructor_staff_user.username,
            'role': 'staff'
        })
        self.assertEqual(len(filtered_response.data['results']), 1)
        self.assertTrue(filtered_response.data['results'][0].startswith(alternate_course2.org))

    def test_no_libraries(self):
        """
        Verify that only Course IDs are returned, not anything else like libraries.
        """
        # Make this user a course staff user for a course, AND a library.
        course_staff_user = self.create_user(username='course_staff', is_staff=False)
        add_users(self.global_admin, CourseStaffRole(self.course.id), course_staff_user)
        add_users(
            self.global_admin,
            CourseStaffRole(LibraryLocator.from_string('library-v1:library_org+library_name')),
            course_staff_user,
        )

        # Requesting the courses should return *only* courses and not libraries.
        self.setup_user(self.staff_user)
        filtered_response = self.verify_response(params={
            'username': course_staff_user.username,
            'role': 'staff'
        })
        self.assertEqual(len(filtered_response.data['results']), 1)
        self.assertTrue(filtered_response.data['results'][0].startswith(self.course.org))


class LazyPageNumberPaginationTestCase(TestCase):

    def test_lazy_page_number_pagination(self):
        number_sequence = range(20)
        even_numbers_lazy_sequence = LazySequence(
            (
                number for number in number_sequence
                if (number % 2) == 0
            ),
            est_len=len(number_sequence)
        )

        expected_response = {
            'results': [10, 12, 14, 16, 18],
            'pagination': {
                'previous': 'http://testserver/endpoint?page_size=5',
                'num_pages': 2,
                'next': None,
                'count': 10}
        }

        request = RequestFactory().get('/endpoint', data={'page': 2, 'page_size': 5})
        request.query_params = {'page': 2, 'page_size': 5}

        pagination = LazyPageNumberPagination()
        pagination.max_page_size = 5
        pagination.page_size = 5
        paginated_queryset = pagination.paginate_queryset(even_numbers_lazy_sequence, request)
        paginated_response = pagination.get_paginated_response(paginated_queryset)
        self.assertDictEqual(expected_response, paginated_response.data)

    def test_not_found_error_for_invalid_page(self):
        number_sequence = range(20)
        even_numbers_lazy_sequence = LazySequence(
            (
                number for number in number_sequence
                if (number % 2) == 0
            ),
            est_len=len(number_sequence)
        )

        request = RequestFactory().get('/endpoint', data={'page': 3, 'page_size': 5})
        request.query_params = {'page': 3, 'page_size': 5}

        with self.assertRaises(Exception) as exc:
            pagination = LazyPageNumberPagination()
            pagination.max_page_size = 5
            pagination.page_size = 5
            paginated_queryset = pagination.paginate_queryset(even_numbers_lazy_sequence, request)
            pagination.get_paginated_response(paginated_queryset)
            self.assertIn('Invalid page', exc.exception)
