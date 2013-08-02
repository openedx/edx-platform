"""
Unit tests for instructor dashboard

Based on (and depends on) unit tests for courseware.

Notes for running by hand:

./manage.py lms --settings test test lms/djangoapps/instructor
"""

from django.test.utils import override_settings

# Need access to internal func to put users in the right group
from django.contrib.auth.models import Group, User

from django.core.urlresolvers import reverse

from courseware.access import _course_staff_group_name
from courseware.tests.helpers import LoginEnrollmentTestCase
from courseware.tests.modulestore_config import TEST_DATA_XML_MODULESTORE
from xmodule.modulestore.django import modulestore
import xmodule.modulestore.django


@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class TestInstructorDashboardGradeDownloadCSV(LoginEnrollmentTestCase):
    '''
    Check for download of csv
    '''

    def setUp(self):
        xmodule.modulestore.django._MODULESTORES = {}

        self.full = modulestore().get_course("edX/full/6.002_Spring_2012")
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
            """ Create an instructor for the course. """
            group_name = _course_staff_group_name(course.location)
            group = Group.objects.create(name=group_name)
            group.user_set.add(User.objects.get(email=self.instructor))

        make_instructor(self.toy)

        self.logout()
        self.login(self.instructor, self.password)
        self.enroll(self.toy)

    def test_download_grades_csv(self):
        course = self.toy
        url = reverse('instructor_dashboard', kwargs={'course_id': course.id})
        msg = "url = {0}\n".format(url)
        response = self.client.post(url, {'action': 'Download CSV of all student grades for this course'})
        msg += "instructor dashboard download csv grades: response = '{0}'\n".format(response)

        self.assertEqual(response['Content-Type'], 'text/csv', msg)

        cdisp = response['Content-Disposition']
        msg += "Content-Disposition = '%s'\n" % cdisp
        self.assertEqual(cdisp, 'attachment; filename=grades_{0}.csv'.format(course.id), msg)

        body = response.content.replace('\r', '')
        msg += "body = '{0}'\n".format(body)

        # All the not-actually-in-the-course hw and labs come from the
        # default grading policy string in graders.py
        expected_body = '''"ID","Username","Full Name","edX email","External email","HW 01","HW 02","HW 03","HW 04","HW 05","HW 06","HW 07","HW 08","HW 09","HW 10","HW 11","HW 12","HW Avg","Lab 01","Lab 02","Lab 03","Lab 04","Lab 05","Lab 06","Lab 07","Lab 08","Lab 09","Lab 10","Lab 11","Lab 12","Lab Avg","Midterm","Final"
"2","u2","username","view2@test.com","","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0"
'''

        self.assertEqual(body, expected_body, msg)
