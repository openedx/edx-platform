"""
Unit tests for instructor dashboard

Based on (and depends on) unit tests for courseware.

Notes for running by hand:

django-admin.py test --settings=lms.envs.test --pythonpath=. lms/djangoapps/instructor
"""

import courseware.tests.tests as ct

from nose import SkipTest
from mock import patch, Mock
from override_settings import override_settings

# Need access to internal func to put users in the right group
from courseware.access import _course_staff_group_name
from django.contrib.auth.models import User, Group
from django.conf import settings
from django.core.urlresolvers import reverse

import xmodule.modulestore.django

from xmodule.modulestore.django import modulestore


@override_settings(MODULESTORE=ct.TEST_DATA_XML_MODULESTORE)
class TestInstructorDashboardGradeDownloadCSV(ct.PageLoader):
    '''
    Check for download of csv
    '''

    def setUp(self):
        xmodule.modulestore.django._MODULESTORES = {}
        courses = modulestore().get_courses()

        def find_course(name):
            """Assumes the course is present"""
            return [c for c in courses if c.location.course==name][0]

        self.full = find_course("full")
        self.toy = find_course("toy")

        # Create two accounts
        self.student = 'view@test.com'
        self.instructor = 'view2@test.com'
        self.password = 'foo'
        self.create_account('u1', self.student, self.password)
        self.create_account('u2', self.instructor, self.password)
        self.activate_user(self.student)
        self.activate_user(self.instructor)

        group_name = _course_staff_group_name(self.toy.location)
        g = Group.objects.create(name=group_name)
        g.user_set.add(ct.user(self.instructor))

        self.logout()
        self.login(self.instructor, self.password)
        self.enroll(self.toy)


    def test_download_grades_csv(self):
        print "running test_download_grades_csv"
        course = self.toy
        url = reverse('instructor_dashboard', kwargs={'course_id': course.id})
        msg = "url = %s\n" % url
        resp = self.client.post(url, {
            'action': 'Download CSV of all student grades for this course',
            })
        msg += "instructor dashboard download csv grades: resp = '%s'" % resp

        respstr = str(resp).replace('\r','')
        respstr = respstr.replace('TT_2012','2012')	# jenkins course_id is TT_2012_Fall instead of 2012_Fall?
        #open('idtest.out','w').write(respstr)

        expected_resp = '''Vary: Cookie
Content-Type: text/csv
Content-Disposition: attachment; filename=grades_edX/toy/2012_Fall.csv
Cache-Control: no-cache, no-store, must-revalidate

"ID","Username","Full Name","edX email","External email","HW 01","HW 02","HW 03","HW 04","HW 05","HW 06","HW 07","HW 08","HW 09","HW 10","HW 11","HW 12","HW Avg","Lab 01","Lab 02","Lab 03","Lab 04","Lab 05","Lab 06","Lab 07","Lab 08","Lab 09","Lab 10","Lab 11","Lab 12","Lab Avg","Midterm","Final"
"2","u2","Fred Weasley","view2@test.com","","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0.0","0.0"
'''

        self.assertEqual(respstr, expected_resp, msg)
