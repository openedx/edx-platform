"""
Unit tests for Edx Proctoring feature flag in new instructor dashboard.
"""

import ddt
from django.conf import settings
from django.core.urlresolvers import reverse
from mock import patch
from nose.plugins.attrib import attr
from six import text_type

from student.roles import CourseStaffRole, CourseInstructorRole
from student.tests.factories import AdminFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@attr(shard=1)
@patch.dict(settings.FEATURES, {'ENABLE_SPECIAL_EXAMS': True})
@ddt.ddt
class TestProctoringDashboardViews(SharedModuleStoreTestCase):
    """
    Check for Proctoring view on the new instructor dashboard
    """
    @classmethod
    def setUpClass(cls):
        super(TestProctoringDashboardViews, cls).setUpClass()
        button = '<button type="button" class="btn-link special_exams" data-section="special_exams">Special Exams</button>'
        cls.proctoring_link = button

    def setUp(self):
        super(TestProctoringDashboardViews, self).setUp()

        # Create instructor account
        self.instructor = AdminFactory.create()
        self.client.login(username=self.instructor.username, password="test")

    def setup_course_url(self, course):
        """
        Create URL for instructor dashboard
        """
        self.url = reverse('instructor_dashboard', kwargs={'course_id': text_type(course.id)})

    def setup_course(self, enable_proctored_exams, enable_timed_exams):
        """
        Create course based on proctored exams and timed exams values
        """
        self.course = CourseFactory.create(enable_proctored_exams=enable_proctored_exams,
                                           enable_timed_exams=enable_timed_exams)
        self.setup_course_url(self.course)

    @ddt.data(
        (True, False),
        (False, True)
    )
    @ddt.unpack
    def test_proctoring_tab_visible_for_global_staff(self, enable_proctored_exams, enable_timed_exams):
        """
        Test Proctoring Tab is visible in the Instructor Dashboard
        for global staff
        """
        self.setup_course(enable_proctored_exams, enable_timed_exams)

        self.instructor.is_staff = True
        self.instructor.save()

        # verify that proctoring tab is visible for global staff
        self._assert_proctoring_tab_is_available()

    @ddt.data(
        (True, False),
        (False, True)
    )
    @ddt.unpack
    def test_proctoring_tab_visible_for_course_staff_and_admin(self, enable_proctored_exams, enable_timed_exams):
        """
        Test Proctoring Tab is visible in the Instructor Dashboard
        for course staff(role of STAFF or ADMIN)
        """
        self.setup_course(enable_proctored_exams, enable_timed_exams)

        self.instructor.is_staff = False
        self.instructor.save()

        # verify that proctoring tab is visible for course staff
        CourseStaffRole(self.course.id).add_users(self.instructor)
        self._assert_proctoring_tab_is_available()

        # verify that proctoring tab is visible for course instructor
        CourseStaffRole(self.course.id).remove_users(self.instructor)
        CourseInstructorRole(self.course.id).add_users(self.instructor)
        self._assert_proctoring_tab_is_available()

    @ddt.data(
        (True, False),
        (False, True)
    )
    @ddt.unpack
    def test_no_proctoring_tab_non_global_staff(self, enable_proctored_exams, enable_timed_exams):
        """
        Test Proctoring Tab is not visible in the Instructor Dashboard
        for course team other than role of staff or admin
        """
        self.setup_course(enable_proctored_exams, enable_timed_exams)

        self.instructor.is_staff = False
        self.instructor.save()

        response = self.client.get(self.url)
        self.assertNotIn(self.proctoring_link, response.content)
        self.assertNotIn('Allowance Section', response.content)

    @patch.dict(settings.FEATURES, {'ENABLE_SPECIAL_EXAMS': False})
    @ddt.data(
        (True, False),
        (False, True)
    )
    @ddt.unpack
    def test_no_tab_flag_unset(self, enable_proctored_exams, enable_timed_exams):
        """
        Special Exams tab will not be visible if special exams settings are not enabled inspite of
        proctored exams or timed exams is enabled
        """
        self.setup_course(enable_proctored_exams, enable_timed_exams)

        self.instructor.is_staff = True
        self.instructor.save()

        response = self.client.get(self.url)
        self.assertNotIn(self.proctoring_link, response.content)
        self.assertNotIn('Allowance Section', response.content)

    def _assert_proctoring_tab_is_available(self):
        """
        Asserts that proctoring tab is available for logged in user.
        """
        response = self.client.get(self.url)
        self.assertIn(self.proctoring_link, response.content)
        self.assertIn('Allowance Section', response.content)
