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
from contentstore.tests.utils import AjaxEnabledTestClient
from student.tests.factories import UserFactory
from student.roles import CourseInstructorRole, CourseStaffRole
from xmodule.modulestore import Location
from xmodule.modulestore.django import loc_mapper
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

TOTAL_COURSES_COUNT = 1000
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
        course = CourseFactory.create(
            org=course_location.org,
            number=course_location.course,
            display_name=course_location.name
        )

        for role in [CourseInstructorRole, CourseStaffRole]:
            # pylint: disable=protected-access
            groupnames = role(course.id)._group_names
            if group_name_format == 'group_name_with_course_name_only':
                # Create role (instructor/staff) groups with course_name only: 'instructor_run'
                group, _ = Group.objects.get_or_create(name=groupnames[2])
            elif group_name_format == 'group_name_with_slashes':
                # Create role (instructor/staff) groups with format: 'instructor_edX/Course/Run'
                # Since "Group.objects.get_or_create(name=groupnames[1])" would have made group with lowercase name
                # so manually create group name of old type
                if role == CourseInstructorRole:
                    group, _ = Group.objects.get_or_create(name=u'{}_{}'.format('instructor', course.id))
                else:
                    group, _ = Group.objects.get_or_create(name=u'{}_{}'.format('staff', course.id))
            else:
                # Create role (instructor/staff) groups with format: 'instructor_edx.course.run'
                group, _ = Group.objects.get_or_create(name=groupnames[0])

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


    # Temporarily disabling this test because it caused the following failure intermittently in Jenkins.
    # Perhaps due to a test ordering or cleanup issue?
    #
    # 1) FAIL: test_course_listing_performance (contentstore.tests.test_course_listing.TestCourseListing)
    #
    #    Traceback (most recent call last):
    #     cms/djangoapps/contentstore/tests/test_course_listing.py line 176 in test_course_listing_performance
    #       self.assertEqual(len(courses_list), USER_COURSES_COUNT)
    #    AssertionError: 49 != 50
    #
    @skip
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
        for number in range(1, TOTAL_COURSES_COUNT):
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
