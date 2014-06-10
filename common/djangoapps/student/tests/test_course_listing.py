"""
Unit tests for getting the list of courses for a user through iterating all courses and
by reversing group name formats.
"""
from mock import patch, Mock

from student.tests.factories import UserFactory
from student.roles import GlobalStaff
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, studio_store_config
from xmodule.modulestore.tests.factories import CourseFactory
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xmodule.modulestore.django import modulestore
from xmodule.error_module import ErrorDescriptor
from django.test.client import Client
from student.models import CourseEnrollment
from student.views import get_course_enrollment_pairs
from django.conf import settings
from django.test.utils import override_settings

TEST_MODULESTORE = studio_store_config(settings.TEST_ROOT / "data")


@override_settings(MODULESTORE=TEST_MODULESTORE)
class TestCourseListing(ModuleStoreTestCase):
    """
    Unit tests for getting the list of courses for a logged in user
    """
    def setUp(self):
        """
        Add a student & teacher
        """
        super(TestCourseListing, self).setUp()

        self.student = UserFactory()
        self.teacher = UserFactory()
        GlobalStaff().add_users(self.teacher)
        self.client = Client()
        self.client.login(username=self.teacher.username, password='test')

    def _create_course_with_access_groups(self, course_location):
        """
        Create dummy course with 'CourseFactory' and enroll the student
        """
        course = CourseFactory.create(
            org=course_location.org,
            number=course_location.course,
            run=course_location.run,
            modulestore=modulestore('direct'),
        )

        CourseEnrollment.enroll(self.student, course.id)

        return course

    def tearDown(self):
        """
        Reverse the setup
        """
        self.client.logout()
        super(TestCourseListing, self).tearDown()

    def test_get_course_list(self):
        """
        Test getting courses
        """
        course_location = SlashSeparatedCourseKey('Org1', 'Course1', 'Run1')
        self._create_course_with_access_groups(course_location)

        # get dashboard
        courses_list = list(get_course_enrollment_pairs(self.student, None, []))
        self.assertEqual(len(courses_list), 1)
        self.assertEqual(courses_list[0][0].id, course_location)

        CourseEnrollment.unenroll(self.student, course_location)
        # get dashboard
        courses_list = list(get_course_enrollment_pairs(self.student, None, []))
        self.assertEqual(len(courses_list), 0)

    def test_errored_course_regular_access(self):
        """
        Test the course list for regular staff when get_course returns an ErrorDescriptor
        """
        course_key = SlashSeparatedCourseKey('Org1', 'Course1', 'Run1')
        self._create_course_with_access_groups(course_key)

        with patch('xmodule.modulestore.mongo.base.MongoKeyValueStore', Mock(side_effect=Exception)):
            self.assertIsInstance(modulestore('direct').get_course(course_key), ErrorDescriptor)

            # get courses through iterating all courses
            courses_list = list(get_course_enrollment_pairs(self.student, None, []))
            self.assertEqual(courses_list, [])

    def test_course_listing_errored_deleted_courses(self):
        """
        Create good courses, courses that won't load, and deleted courses which still have
        roles. Test course listing.
        """
        good_location = SlashSeparatedCourseKey('testOrg', 'testCourse', 'RunBabyRun')
        self._create_course_with_access_groups(good_location)

        course_location = SlashSeparatedCourseKey('testOrg', 'doomedCourse', 'RunBabyRun')
        self._create_course_with_access_groups(course_location)
        modulestore('direct').delete_course(course_location)

        course_location = SlashSeparatedCourseKey('testOrg', 'erroredCourse', 'RunBabyRun')
        course = self._create_course_with_access_groups(course_location)
        course_db_record = modulestore('direct')._find_one(course.location)
        course_db_record.setdefault('metadata', {}).get('tabs', []).append({"type": "wiko", "name": "Wiki" })
        modulestore('direct').collection.update(
            {'_id': course.location.to_deprecated_son()},
            {'$set': {
                'metadata.tabs': course_db_record['metadata']['tabs'],
            }},
        )

        courses_list = list(get_course_enrollment_pairs(self.student, None, []))
        self.assertEqual(len(courses_list), 1, courses_list)
        self.assertEqual(courses_list[0][0].id, good_location)
