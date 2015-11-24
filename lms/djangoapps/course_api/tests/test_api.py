"""
Test for course API
"""

from datetime import datetime
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from rest_framework.exceptions import NotFound, PermissionDenied

from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase, ModuleStoreTestCase
from xmodule.course_module import DEFAULT_START_DATE

from ..api import course_detail, list_courses
from .mixins import CourseApiFactoryMixin


class CourseApiTestMixin(CourseApiFactoryMixin):
    """
    Establish basic functionality for Course API tests
    """

    maxDiff = 5000  # long enough to show mismatched dicts

    expected_course_data = {
        'course_id': u'edX/toy/2012_Fall',
        'name': u'Toy Course',
        'number': u'toy',
        'org': u'edX',
        'description': u'A course about toys.',
        'media': {
            'course_image': {
                'uri': u'/c4x/edX/toy/asset/just_a_test.jpg',
            }
        },
        'start': u'2015-07-17T12:00:00Z',
        'start_type': u'timestamp',
        'start_display': u'July 17, 2015',
        'end': u'2015-09-19T18:00:00Z',
        'enrollment_start': u'2015-06-15T00:00:00Z',
        'enrollment_end': u'2015-07-15T00:00:00Z',
        'blocks_url': '/api/courses/v1/blocks/?course_id=edX%2Ftoy%2F2012_Fall',
    }

    @classmethod
    def setUpClass(cls):
        super(CourseApiTestMixin, cls).setUpClass()
        cls.request_factory = RequestFactory()


class CourseDetailTestMixin(CourseApiTestMixin):
    """
    Common functionality for course_detail tests
    """
    def _make_api_call(self, requesting_user, target_user, course_key):
        """
        Call the `course_detail` api endpoint to get information on the course
        identified by `course_key`.
        """
        request = self.request_factory.get('/')
        request.user = requesting_user
        return course_detail(request, target_user, course_key)


class TestGetCourseDetail(CourseDetailTestMixin, SharedModuleStoreTestCase):
    """
    Test course_detail api function
    """
    @classmethod
    def setUpClass(cls):
        super(TestGetCourseDetail, cls).setUpClass()
        cls.course = cls.create_course()
        cls.hidden_course = cls.create_course(course=u'hidden', visible_to_staff_only=True)
        cls.honor_user = cls.create_user('honor', is_staff=False)
        cls.staff_user = cls.create_user('staff', is_staff=True)

    def test_get_existing_course(self):
        result = self._make_api_call(self.honor_user, self.honor_user.username, self.course.id)
        self.assertEqual(self.expected_course_data, result)

    def test_get_nonexistent_course(self):
        course_key = CourseKey.from_string(u'edX/toy/nope')
        with self.assertRaises(NotFound):
            self._make_api_call(self.honor_user, self.honor_user.username, course_key)

    def test_hidden_course_for_honor(self):
        with self.assertRaises(NotFound):
            self._make_api_call(self.honor_user, self.honor_user.username, self.hidden_course.id)

    def test_hidden_course_for_staff(self):
        result = self._make_api_call(self.staff_user, self.staff_user.username, self.hidden_course.id)
        self.assertIsInstance(result, dict)
        self.assertEqual(result['course_id'], u'edX/hidden/2012_Fall')

    def test_hidden_course_for_staff_as_honor(self):
        with self.assertRaises(NotFound):
            self._make_api_call(self.staff_user, self.honor_user.username, self.hidden_course.id)


class TestGetCourseDetailStartDate(CourseDetailTestMixin, ModuleStoreTestCase):
    """
    Test variations of start_date field responses
    """

    def setUp(self):
        super(TestGetCourseDetailStartDate, self).setUp()
        self.staff_user = self.create_user('staff', is_staff=True)

    def test_course_with_advertised_start(self):
        course = self.create_course(
            course=u'custom',
            start=datetime(2015, 3, 15),
            advertised_start=u'The Ides of March'
        )
        result = self._make_api_call(self.staff_user, self.staff_user.username, course.id)
        self.assertEqual(result['course_id'], u'edX/custom/2012_Fall')
        self.assertEqual(result['start_type'], u'string')
        self.assertEqual(result['start_display'], u'The Ides of March')

    def test_course_with_empty_start_date(self):
        course = self.create_course(start=DEFAULT_START_DATE, course=u'custom2')
        result = self._make_api_call(self.staff_user, self.staff_user.username, course.id)
        self.assertEqual(result['course_id'], u'edX/custom2/2012_Fall')
        self.assertEqual(result['start_type'], u'empty')
        self.assertIsNone(result['start_display'])


class CourseListTestMixin(CourseApiTestMixin):
    """
    Common behavior for list_courses tests
    """
    def _make_api_call(self, requesting_user, specified_user):
        """
        Call the list_courses api endpoint to get information about
        `specified_user` on behalf of `requesting_user`.
        """
        request = self.request_factory.get('/')
        request.user = requesting_user
        return list_courses(request, specified_user.username)


class TestGetCourseList(CourseListTestMixin, SharedModuleStoreTestCase):
    """
    Test the behavior of the `list_courses` api function.
    """
    @classmethod
    def setUpClass(cls):
        super(TestGetCourseList, cls).setUpClass()
        cls.create_course()
        cls.staff_user = cls.create_user("staff", is_staff=True)
        cls.honor_user = cls.create_user("honor", is_staff=False)

    def test_as_staff(self):
        courses = self._make_api_call(self.staff_user, self.staff_user)
        self.assertEqual(len(courses), 1)
        self.assertEqual(courses[0], self.expected_course_data)

    def test_for_honor_user_as_staff(self):
        courses = self._make_api_call(self.staff_user, self.honor_user)
        self.assertEqual(len(courses), 1)
        self.assertEqual(courses[0], self.expected_course_data)

    def test_as_honor(self):
        courses = self._make_api_call(self.honor_user, self.honor_user)
        self.assertEqual(len(courses), 1)
        self.assertEqual(courses[0], self.expected_course_data)

    def test_for_staff_user_as_honor(self):
        with self.assertRaises(PermissionDenied):
            self._make_api_call(self.honor_user, self.staff_user)

    def test_as_anonymous(self):
        anonuser = AnonymousUser()
        courses = self._make_api_call(anonuser, anonuser)
        self.assertEqual(len(courses), 1)
        self.assertEqual(courses[0], self.expected_course_data)

    def test_for_honor_user_as_anonymous(self):
        anonuser = AnonymousUser()
        with self.assertRaises(PermissionDenied):
            self._make_api_call(anonuser, self.staff_user)

    def test_multiple_courses(self):
        self.create_course(course='second')
        courses = self._make_api_call(self.honor_user, self.honor_user)
        self.assertEqual(len(courses), 2)


class TestGetCourseListExtras(CourseListTestMixin, ModuleStoreTestCase):
    """
    Tests of course_list api function that require alternative configurations
    of created courses.
    """
    @classmethod
    def setUpClass(cls):
        super(TestGetCourseListExtras, cls).setUpClass()
        cls.staff_user = cls.create_user("staff", is_staff=True)
        cls.honor_user = cls.create_user("honor", is_staff=False)

    def test_no_courses(self):
        courses = self._make_api_call(self.honor_user, self.honor_user)
        self.assertEqual(len(courses), 0)

    def test_hidden_course_for_honor(self):
        self.create_course(visible_to_staff_only=True)
        courses = self._make_api_call(self.honor_user, self.honor_user)
        self.assertEqual(len(courses), 0)

    def test_hidden_course_for_staff(self):
        self.create_course(visible_to_staff_only=True)
        courses = self._make_api_call(self.staff_user, self.staff_user)
        self.assertEqual(len(courses), 1)
        self.assertEqual(courses[0], self.expected_course_data)
