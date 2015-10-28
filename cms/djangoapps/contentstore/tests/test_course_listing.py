"""
Unit tests for getting the list of courses for a user through iterating all courses and
by reversing group name formats.
"""
import random

from chrono import Timer
from mock import patch, Mock
import ddt

from django.test import RequestFactory

from contentstore.views.course import _accessible_courses_list, _accessible_courses_list_from_groups, AccessListFallback
from contentstore.utils import delete_course_and_groups
from contentstore.tests.utils import AjaxEnabledTestClient
from student.tests.factories import UserFactory
from student.roles import CourseInstructorRole, CourseStaffRole, GlobalStaff, OrgStaffRole, OrgInstructorRole
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, check_mongo_calls
from xmodule.modulestore import ModuleStoreEnum
from opaque_keys.edx.locations import CourseLocator
from xmodule.modulestore.django import modulestore
from xmodule.error_module import ErrorDescriptor
from course_action_state.models import CourseRerunState

TOTAL_COURSES_COUNT = 500
USER_COURSES_COUNT = 50


@ddt.ddt
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
        # create and log in a non-staff user
        self.user = UserFactory()
        self.factory = RequestFactory()
        self.request = self.factory.get('/course')
        self.request.user = self.user
        self.client = AjaxEnabledTestClient()
        self.client.login(username=self.user.username, password='test')

    def _create_course_with_access_groups(self, course_location, user=None):
        """
        Create dummy course with 'CourseFactory' and role (instructor/staff) groups
        """
        course = CourseFactory.create(
            org=course_location.org,
            number=course_location.course,
            run=course_location.run,
            default_store=ModuleStoreEnum.Type.mongo
        )

        if user is not None:
            for role in [CourseInstructorRole, CourseStaffRole]:
                role(course.id).add_users(user)

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
        course_location = self.store.make_course_key('Org1', 'Course1', 'Run1')
        self._create_course_with_access_groups(course_location, self.user)

        # get courses through iterating all courses
        courses_list, __ = _accessible_courses_list(self.request)
        self.assertEqual(len(courses_list), 1)

        # get courses by reversing group name formats
        courses_list_by_groups, __ = _accessible_courses_list_from_groups(self.request)
        self.assertEqual(len(courses_list_by_groups), 1)
        # check both course lists have same courses
        self.assertEqual(courses_list, courses_list_by_groups)

    def test_errored_course_global_staff(self):
        """
        Test the course list for global staff when get_course returns an ErrorDescriptor
        """
        GlobalStaff().add_users(self.user)

        course_key = self.store.make_course_key('Org1', 'Course1', 'Run1')
        self._create_course_with_access_groups(course_key, self.user)

        with patch('xmodule.modulestore.mongo.base.MongoKeyValueStore', Mock(side_effect=Exception)):
            self.assertIsInstance(modulestore().get_course(course_key), ErrorDescriptor)

            # get courses through iterating all courses
            courses_list, __ = _accessible_courses_list(self.request)
            self.assertEqual(courses_list, [])

            # get courses by reversing group name formats
            courses_list_by_groups, __ = _accessible_courses_list_from_groups(self.request)
            self.assertEqual(courses_list_by_groups, [])

    def test_errored_course_regular_access(self):
        """
        Test the course list for regular staff when get_course returns an ErrorDescriptor
        """
        GlobalStaff().remove_users(self.user)
        CourseStaffRole(self.store.make_course_key('Non', 'Existent', 'Course')).add_users(self.user)

        course_key = self.store.make_course_key('Org1', 'Course1', 'Run1')
        self._create_course_with_access_groups(course_key, self.user)

        with patch('xmodule.modulestore.mongo.base.MongoKeyValueStore', Mock(side_effect=Exception)):
            self.assertIsInstance(modulestore().get_course(course_key), ErrorDescriptor)

            # get courses through iterating all courses
            courses_list, __ = _accessible_courses_list(self.request)
            self.assertEqual(courses_list, [])

            # get courses by reversing group name formats
            courses_list_by_groups, __ = _accessible_courses_list_from_groups(self.request)
            self.assertEqual(courses_list_by_groups, [])
            self.assertEqual(courses_list, courses_list_by_groups)

    def test_get_course_list_with_invalid_course_location(self):
        """
        Test getting courses with invalid course location (course deleted from modulestore).
        """
        course_key = self.store.make_course_key('Org', 'Course', 'Run')
        self._create_course_with_access_groups(course_key, self.user)

        # get courses through iterating all courses
        courses_list, __ = _accessible_courses_list(self.request)
        self.assertEqual(len(courses_list), 1)

        # get courses by reversing group name formats
        courses_list_by_groups, __ = _accessible_courses_list_from_groups(self.request)
        self.assertEqual(len(courses_list_by_groups), 1)
        # check both course lists have same courses
        self.assertEqual(courses_list, courses_list_by_groups)

        # now delete this course and re-add user to instructor group of this course
        delete_course_and_groups(course_key, self.user.id)

        CourseInstructorRole(course_key).add_users(self.user)

        # test that get courses through iterating all courses now returns no course
        courses_list, __ = _accessible_courses_list(self.request)
        self.assertEqual(len(courses_list), 0)

    def test_course_listing_performance(self):
        """
        Create large number of courses and give access of some of these courses to the user and
        compare the time to fetch accessible courses for the user through traversing all courses and
        reversing django groups
        """
        # create list of random course numbers which will be accessible to the user
        user_course_ids = random.sample(range(TOTAL_COURSES_COUNT), USER_COURSES_COUNT)

        # create courses and assign those to the user which have their number in user_course_ids
        for number in range(TOTAL_COURSES_COUNT):
            org = 'Org{0}'.format(number)
            course = 'Course{0}'.format(number)
            run = 'Run{0}'.format(number)
            course_location = self.store.make_course_key(org, course, run)
            if number in user_course_ids:
                self._create_course_with_access_groups(course_location, self.user)
            else:
                self._create_course_with_access_groups(course_location)

        # time the get courses by iterating through all courses
        with Timer() as iteration_over_courses_time_1:
            courses_list, __ = _accessible_courses_list(self.request)
        self.assertEqual(len(courses_list), USER_COURSES_COUNT)

        # time again the get courses by iterating through all courses
        with Timer() as iteration_over_courses_time_2:
            courses_list, __ = _accessible_courses_list(self.request)
        self.assertEqual(len(courses_list), USER_COURSES_COUNT)

        # time the get courses by reversing django groups
        with Timer() as iteration_over_groups_time_1:
            courses_list, __ = _accessible_courses_list_from_groups(self.request)
        self.assertEqual(len(courses_list), USER_COURSES_COUNT)

        # time again the get courses by reversing django groups
        with Timer() as iteration_over_groups_time_2:
            courses_list, __ = _accessible_courses_list_from_groups(self.request)
        self.assertEqual(len(courses_list), USER_COURSES_COUNT)

        # test that the time taken by getting courses through reversing django groups is lower then the time
        # taken by traversing through all courses (if accessible courses are relatively small)
        self.assertGreaterEqual(iteration_over_courses_time_1.elapsed, iteration_over_groups_time_1.elapsed)
        self.assertGreaterEqual(iteration_over_courses_time_2.elapsed, iteration_over_groups_time_2.elapsed)

        # Now count the db queries
        with check_mongo_calls(USER_COURSES_COUNT):
            _accessible_courses_list_from_groups(self.request)

        # Calls:
        #    1) query old mongo
        #    2) get_more on old mongo
        #    3) query split (but no courses so no fetching of data)
        with check_mongo_calls(3):
            _accessible_courses_list(self.request)

    def test_course_listing_errored_deleted_courses(self):
        """
        Create good courses, courses that won't load, and deleted courses which still have
        roles. Test course listing.
        """
        store = modulestore()._get_modulestore_by_type(ModuleStoreEnum.Type.mongo)

        course_location = self.store.make_course_key('testOrg', 'testCourse', 'RunBabyRun')
        self._create_course_with_access_groups(course_location, self.user)

        course_location = self.store.make_course_key('testOrg', 'doomedCourse', 'RunBabyRun')
        self._create_course_with_access_groups(course_location, self.user)
        store.delete_course(course_location, self.user.id)

        courses_list, __ = _accessible_courses_list_from_groups(self.request)
        self.assertEqual(len(courses_list), 1, courses_list)

    @ddt.data(OrgStaffRole('AwesomeOrg'), OrgInstructorRole('AwesomeOrg'))
    def test_course_listing_org_permissions(self, role):
        """
        Create multiple courses within the same org.  Verify that someone with org-wide permissions can access
        all of them.
        """
        org_course_one = self.store.make_course_key('AwesomeOrg', 'Course1', 'RunBabyRun')
        CourseFactory.create(
            org=org_course_one.org,
            number=org_course_one.course,
            run=org_course_one.run
        )

        org_course_two = self.store.make_course_key('AwesomeOrg', 'Course2', 'RunRunRun')
        CourseFactory.create(
            org=org_course_two.org,
            number=org_course_two.course,
            run=org_course_two.run
        )

        # Two types of org-wide roles have edit permissions: staff and instructor.  We test both
        role.add_users(self.user)

        with self.assertRaises(AccessListFallback):
            _accessible_courses_list_from_groups(self.request)
        courses_list, __ = _accessible_courses_list(self.request)
        self.assertEqual(len(courses_list), 2)

    def test_course_listing_with_actions_in_progress(self):
        sourse_course_key = CourseLocator('source-Org', 'source-Course', 'source-Run')

        num_courses_to_create = 3
        courses = [
            self._create_course_with_access_groups(CourseLocator('Org', 'CreatedCourse' + str(num), 'Run'), self.user)
            for num in range(num_courses_to_create)
        ]
        courses_in_progress = [
            self._create_course_with_access_groups(CourseLocator('Org', 'InProgressCourse' + str(num), 'Run'), self.user)
            for num in range(num_courses_to_create)
        ]

        # simulate initiation of course actions
        for course in courses_in_progress:
            CourseRerunState.objects.initiated(
                sourse_course_key, destination_course_key=course.id, user=self.user, display_name="test course"
            )

        # verify return values
        for method in (_accessible_courses_list_from_groups, _accessible_courses_list):
            def set_of_course_keys(course_list, key_attribute_name='id'):
                """Returns a python set of course keys by accessing the key with the given attribute name."""
                return set(getattr(c, key_attribute_name) for c in course_list)

            found_courses, unsucceeded_course_actions = method(self.request)
            self.assertSetEqual(set_of_course_keys(courses + courses_in_progress), set_of_course_keys(found_courses))
            self.assertSetEqual(
                set_of_course_keys(courses_in_progress), set_of_course_keys(unsucceeded_course_actions, 'course_key')
            )
