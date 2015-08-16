"""
Unit tests for Edx Proctoring feature flag in new instructor dashboard.
"""

from mock import patch

from django.conf import settings
from django.core.urlresolvers import reverse
from nose.plugins.attrib import attr

from student.roles import CourseFinanceAdminRole
from student.tests.factories import AdminFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@attr('shard_1')
@patch.dict(settings.FEATURES, {'ENABLE_PROCTORED_EXAMS': True})
class TestProctoringDashboardViews(ModuleStoreTestCase):
    """
    Check for Proctoring view on the new instructor dashboard
    """
    def setUp(self):
        super(TestProctoringDashboardViews, self).setUp()
        self.course = CourseFactory.create()
        self.course.enable_proctored_exams = True

        # Create instructor account
        self.instructor = AdminFactory.create()
        self.client.login(username=self.instructor.username, password="test")
        self.course = self.update_course(self.course, self.instructor.id)

        # URL for instructor dash
        self.url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id.to_deprecated_string()})
        self.proctoring_link = '<a href="" data-section="proctoring">Proctoring</a>'
        CourseFinanceAdminRole(self.course.id).add_users(self.instructor)

    def test_pass_proctoring_tab_in_instructor_dashboard(self):
        """
        Test Pass Proctoring Tab is in the Instructor Dashboard
        """
        self.instructor.is_staff = True
        self.instructor.save()

        response = self.client.get(self.url)
        self.assertTrue(self.proctoring_link in response.content)
        self.assertTrue('Allowance Section' in response.content)

    def test_no_tab_non_global_staff(self):
        """
        Test Pass Proctoring Tab is not in the Instructor Dashboard
        for non global staff users
        """
        self.instructor.is_staff = False
        self.instructor.save()

        response = self.client.get(self.url)
        self.assertFalse(self.proctoring_link in response.content)
        self.assertFalse('Allowance Section' in response.content)

    @patch.dict(settings.FEATURES, {'ENABLE_PROCTORED_EXAMS': False})
    def test_no_tab_flag_unset(self):
        """
        Test Pass Proctoring Tab is not in the Instructor Dashboard
        if the feature flag 'ENABLE_PROCTORED_EXAMS' is unset.
        """
        self.instructor.is_staff = True
        self.instructor.save()

        response = self.client.get(self.url)
        self.assertFalse(self.proctoring_link in response.content)
        self.assertFalse('Allowance Section' in response.content)
