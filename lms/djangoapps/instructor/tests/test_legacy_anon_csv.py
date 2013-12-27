"""
Unit tests for instructor dashboard

Based on (and depends on) unit tests for courseware.

Notes for running by hand:

./manage.py lms --settings test test lms/djangoapps/instructor
"""

from django.test.utils import override_settings

# Need access to internal func to put users in the right group
from django.contrib.auth.models import User

from django.core.urlresolvers import reverse

from courseware.tests.helpers import LoginEnrollmentTestCase
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from student.roles import CourseStaffRole
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.django import modulestore, clear_existing_modulestores

from mock import patch


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestInstructorDashboardAnonCSV(ModuleStoreTestCase, LoginEnrollmentTestCase):
    '''
    Check for download of csv
    '''

    # Note -- I copied this setUp from a similar test
    def setUp(self):
        clear_existing_modulestores()
        self.toy = modulestore().get_course("edX/toy/2012_Fall")

        # Create two accounts
        self.student = 'view@test.com'
        self.instructor = 'view2@test.com'
        self.password = 'foo'
        self.create_account('u1', self.student, self.password)
        self.create_account('u2', self.instructor, self.password)
        self.activate_user(self.student)
        self.activate_user(self.instructor)

        def make_instructor(course):
            """ Create an instructor for the course."""
            CourseStaffRole(course.location).add_users(User.objects.get(email=self.instructor))

        make_instructor(self.toy)

        self.logout()
        self.login(self.instructor, self.password)
        self.enroll(self.toy)

    def test_download_anon_csv(self):
        course = self.toy
        url = reverse('instructor_dashboard', kwargs={'course_id': course.id})

        with patch('instructor.views.legacy.unique_id_for_user') as mock_unique:
            mock_unique.return_value = 42
            response = self.client.post(url, {'action': 'Download CSV of all student anonymized IDs'})

        self.assertEqual(response['Content-Type'], 'text/csv')
        body = response.content.replace('\r', '')
        self.assertEqual(body, '"User ID","Anonymized user ID"\n"2","42"\n')
