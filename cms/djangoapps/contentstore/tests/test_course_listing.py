"""
Unit tests for getting the list of courses for a user through iterating all courses and
by reversing group name formats.
"""
import random
from chrono import Timer
from unittest import skip

from django.contrib.auth.models import Group
from django.test import RequestFactory

from contentstore.views.course import _accessible_courses_list, _accessible_courses_list_from_groups
from contentstore.utils import delete_course_and_groups
from contentstore.tests.utils import AjaxEnabledTestClient
from student.tests.factories import UserFactory
from student.roles import CourseInstructorRole, CourseStaffRole
from xmodule.modulestore import Location
from xmodule.modulestore.django import loc_mapper
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

TOTAL_COURSES_COUNT = 500
USER_COURSES_COUNT = 50


class TestCourseListing(ModuleStoreTestCase):
    """
    Unit tests for getting the list of courses for a logged in user
    """
    def setUp(self):
        """
        Add a user and a course
        """
        super(TestCourseListing, self).setUp()
        # create and log in a staff user.
        self.user = UserFactory(is_staff=True)  # pylint: disable=no-member
        self.factory = RequestFactory()
        self.client = AjaxEnabledTestClient()
        self.client.login(username=self.user.username, password='test')

    def _create_course_with_access_groups(self, course_location, group_name_format='group_name_with_dots', user=None):
        """
        Create dummy course with 'CourseFactory' and role (instructor/staff) groups with provided group_name_format
        """
        course_locator = loc_mapper().translate_location(
            course_location.course_id, course_location, False, True
        )
        course = CourseFactory.create(
            org=course_location.org,
            number=course_location.course,
            display_name=course_location.name
        )

        for role in [CourseInstructorRole, CourseStaffRole]:
            # pylint: disable=protected-access
            groupnames = role(course_locator)._group_names
            if group_name_format == 'group_name_with_course_name_only':
                # Create role (instructor/staff) groups with course_name only: 'instructor_run'
                group, __ = Group.objects.get_or_create(name=groupnames[2])
            elif group_name_format == 'group_name_with_slashes':
                # Create role (instructor/staff) groups with format: 'instructor_edX/Course/Run'
                # Since "Group.objects.get_or_create(name=groupnames[1])" would have made group with lowercase name
                # so manually create group name of old type
                if role == CourseInstructorRole:
                    group, __ = Group.objects.get_or_create(name=u'{}_{}'.format('instructor', course_location.course_id))
                else:
                    group, __ = Group.objects.get_or_create(name=u'{}_{}'.format('staff', course_location.course_id))
            else:
                # Create role (instructor/staff) groups with format: 'instructor_edx.course.run'
                group, __ = Group.objects.get_or_create(name=groupnames[0])

            if user is not None:
                user.groups.add(group)
        return course

    def tearDown(self):
        """
        Reverse the setup
        """
        self.client.logout()
        ModuleStoreTestCase.tearDown(self)

    def test_get_course_list(self):
        """
        Test getting courses with new access group format e.g. 'instructor_edx.course.run'
        """
        request = self.factory.get('/course')
        request.user = self.user

        course_location = Location(['i4x', 'Org1', 'Course1', 'course', 'Run1'])
        self._create_course_with_access_groups(course_location, 'group_name_with_dots', self.user)

        # get courses through iterating all courses
        courses_list = _accessible_courses_list(request)
        self.assertEqual(len(courses_list), 1)

        # get courses by reversing group name formats
        courses_list_by_groups = _accessible_courses_list_from_groups(request)
        self.assertEqual(len(courses_list_by_groups), 1)
        # check both course lists have same courses
        self.assertEqual(courses_list, courses_list_by_groups)

    def test_get_course_list_with_old_group_formats(self):
        """
        Test getting all courses with old course role (instructor/staff) groups
        """
        request = self.factory.get('/course')
        request.user = self.user

        # create a course with new groups name format e.g. 'instructor_edx.course.run'
        course_location = Location(['i4x', 'Org_1', 'Course_1', 'course', 'Run_1'])
        self._create_course_with_access_groups(course_location, 'group_name_with_dots', self.user)

        # create a course with old groups name format e.g. 'instructor_edX/Course/Run'
        old_course_location = Location(['i4x', 'Org_2', 'Course_2', 'course', 'Run_2'])
        self._create_course_with_access_groups(old_course_location, 'group_name_with_slashes', self.user)

        # get courses through iterating all courses
        courses_list = _accessible_courses_list(request)
        self.assertEqual(len(courses_list), 2)

        # get courses by reversing groups name
        courses_list_by_groups = _accessible_courses_list_from_groups(request)
        self.assertEqual(len(courses_list_by_groups), 2)

        # create a new course with older group name format (with dots in names) e.g. 'instructor_edX/Course.name/Run.1'
        old_course_location = Location(['i4x', 'Org.Foo.Bar', 'Course.number', 'course', 'Run.name'])
        self._create_course_with_access_groups(old_course_location, 'group_name_with_slashes', self.user)
        # get courses through iterating all courses
        courses_list = _accessible_courses_list(request)
        self.assertEqual(len(courses_list), 3)
        # get courses by reversing group name formats
        courses_list_by_groups = _accessible_courses_list_from_groups(request)
        self.assertEqual(len(courses_list_by_groups), 3)

        # create a new course with older group name format e.g. 'instructor_Run'
        old_course_location = Location(['i4x', 'Org_3', 'Course_3', 'course', 'Run_3'])
        self._create_course_with_access_groups(old_course_location, 'group_name_with_course_name_only', self.user)

        # get courses through iterating all courses
        courses_list = _accessible_courses_list(request)
        self.assertEqual(len(courses_list), 4)

        # should raise an exception for getting courses with older format of access group by reversing django groups
        with self.assertRaises(ItemNotFoundError):
            courses_list_by_groups = _accessible_courses_list_from_groups(request)

    def test_course_listing_performance(self):
        """
        Create large number of courses and give access of some of these courses to the user and
        compare the time to fetch accessible courses for the user through traversing all courses and
        reversing django groups
        """
        # create and log in a non-staff user
        self.user = UserFactory()
        request = self.factory.get('/course')
        request.user = self.user
        self.client.login(username=self.user.username, password='test')

        # create list of random course numbers which will be accessible to the user
        user_course_ids = random.sample(range(TOTAL_COURSES_COUNT), USER_COURSES_COUNT)

        # create courses and assign those to the user which have their number in user_course_ids
        for number in range(TOTAL_COURSES_COUNT):
            org = 'Org{0}'.format(number)
            course = 'Course{0}'.format(number)
            run = 'Run{0}'.format(number)
            course_location = Location(['i4x', org, course, 'course', run])
            if number in user_course_ids:
                self._create_course_with_access_groups(course_location, 'group_name_with_dots', self.user)
            else:
                self._create_course_with_access_groups(course_location, 'group_name_with_dots')

        # time the get courses by iterating through all courses
        with Timer() as iteration_over_courses_time_1:
            courses_list = _accessible_courses_list(request)
        self.assertEqual(len(courses_list), USER_COURSES_COUNT)

        # time again the get courses by iterating through all courses
        with Timer() as iteration_over_courses_time_2:
            courses_list = _accessible_courses_list(request)
        self.assertEqual(len(courses_list), USER_COURSES_COUNT)

        # time the get courses by reversing django groups
        with Timer() as iteration_over_groups_time_1:
            courses_list = _accessible_courses_list_from_groups(request)
        self.assertEqual(len(courses_list), USER_COURSES_COUNT)

        # time again the get courses by reversing django groups
        with Timer() as iteration_over_groups_time_2:
            courses_list = _accessible_courses_list_from_groups(request)
        self.assertEqual(len(courses_list), USER_COURSES_COUNT)

        # test that the time taken by getting courses through reversing django groups is lower then the time
        # taken by traversing through all courses (if accessible courses are relatively small)
        self.assertGreaterEqual(iteration_over_courses_time_1.elapsed, iteration_over_groups_time_1.elapsed)
        self.assertGreaterEqual(iteration_over_courses_time_2.elapsed, iteration_over_groups_time_2.elapsed)

    def test_get_course_list_with_same_course_id(self):
        """
        Test getting courses with same id but with different name case. Then try to delete one of them and
        check that it is properly deleted and other one is accessible
        """
        request = self.factory.get('/course')
        request.user = self.user

        course_location_caps = Location(['i4x', 'Org', 'COURSE', 'course', 'Run'])
        self._create_course_with_access_groups(course_location_caps, 'group_name_with_dots', self.user)

        # get courses through iterating all courses
        courses_list = _accessible_courses_list(request)
        self.assertEqual(len(courses_list), 1)

        # get courses by reversing group name formats
        courses_list_by_groups = _accessible_courses_list_from_groups(request)
        self.assertEqual(len(courses_list_by_groups), 1)
        # check both course lists have same courses
        self.assertEqual(courses_list, courses_list_by_groups)

        # now create another course with same course_id but different name case
        course_location_camel = Location(['i4x', 'Org', 'Course', 'course', 'Run'])
        self._create_course_with_access_groups(course_location_camel, 'group_name_with_dots', self.user)

        # test that get courses through iterating all courses returns both courses
        courses_list = _accessible_courses_list(request)
        self.assertEqual(len(courses_list), 2)

        # test that get courses by reversing group name formats returns only one course
        courses_list_by_groups = _accessible_courses_list_from_groups(request)
        self.assertEqual(len(courses_list_by_groups), 1)

        course_locator = loc_mapper().translate_location(course_location_caps.course_id, course_location_caps)
        outline_url = course_locator.url_reverse('course/')
        # now delete first course (course_location_caps) and check that it is no longer accessible
        delete_course_and_groups(course_location_caps.course_id, commit=True)
        # add user to this course instructor group since he was removed from that group on course delete
        instructor_group_name = CourseInstructorRole(course_locator)._group_names[0]  # pylint: disable=protected-access
        group, __ = Group.objects.get_or_create(name=instructor_group_name)
        self.user.groups.add(group)

        # test that get courses through iterating all courses now returns one course
        courses_list = _accessible_courses_list(request)
        self.assertEqual(len(courses_list), 1)

        # test that get courses by reversing group name formats also returns one course
        courses_list_by_groups = _accessible_courses_list_from_groups(request)
        self.assertEqual(len(courses_list_by_groups), 1)

        # now check that deleted course in not accessible
        response = self.client.get(outline_url, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 403)

        # now check that other course in accessible
        course_locator = loc_mapper().translate_location(course_location_camel.course_id, course_location_camel)
        outline_url = course_locator.url_reverse('course/')
        response = self.client.get(outline_url, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
