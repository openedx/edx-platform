"""
Unit tests for Edx Proctoring feature flag in new instructor dashboard.
"""

from mock import patch

from django.conf import settings
from django.core.urlresolvers import reverse
from nose.plugins.attrib import attr

from student.roles import CourseFinanceAdminRole
from student.tests.factories import AdminFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@attr('shard_1')
@patch.dict(settings.FEATURES, {'ENABLE_SPECIAL_EXAMS': True})
class TestProctoringDashboardViews(SharedModuleStoreTestCase):
    """
    Check for Proctoring view on the new instructor dashboard
    """
    @classmethod
    def setUpClass(cls):
        super(TestProctoringDashboardViews, cls).setUpClass()
        cls.course = CourseFactory.create(enable_proctored_exams=True)

        # URL for instructor dash
        cls.url = reverse('instructor_dashboard', kwargs={'course_id': cls.course.id.to_deprecated_string()})
        cls.proctoring_link = '<a href="" data-section="special_exams">Special Exams</a>'

    def setUp(self):
        super(TestProctoringDashboardViews, self).setUp()

        # Create instructor account
        self.instructor = AdminFactory.create()
        self.client.login(username=self.instructor.username, password="test")

        CourseFinanceAdminRole(self.course.id).add_users(self.instructor)

    def test_pass_proctoring_tab_in_instructor_dashboard(self):
        """
        Test Pass Proctoring Tab is in the Instructor Dashboard
        """
        self.instructor.is_staff = True
        self.instructor.save()

        response = self.client.get(self.url)
        self.assertIn(self.proctoring_link, response.content)
        self.assertIn('Allowance Section', response.content)

    def test_no_tab_non_global_staff(self):
        """
        Test Pass Proctoring Tab is not in the Instructor Dashboard
        for non global staff users
        """
        self.instructor.is_staff = False
        self.instructor.save()

        response = self.client.get(self.url)
        self.assertNotIn(self.proctoring_link, response.content)
        self.assertNotIn('Allowance Section', response.content)

    @patch.dict(settings.FEATURES, {'ENABLE_SPECIAL_EXAMS': False})
    def test_no_tab_flag_unset(self):
        """
        Special Exams tab will not be visible if
        the user is not a staff member.
        """
        self.instructor.is_staff = True
        self.instructor.save()

        response = self.client.get(self.url)
        self.assertNotIn(self.proctoring_link, response.content)
        self.assertNotIn('Allowance Section', response.content)
