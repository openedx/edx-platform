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
            group_name = _course_staff_group_name(course.location)
            g = Group.objects.create(name=group_name)
            g.user_set.add(ct.user(self.instructor))

        make_instructor(self.toy)

        self.logout()
        self.login(self.instructor, self.password)
        self.enroll(self.toy)


    def test_download_grades_csv(self):
        print "running test_download_grades_csv"
        toy = self.toy
        self.check_download_grades_csv(toy, toy.id in settings.INTERNAL_COURSE_IDS)


    @override_settings(INTERNAL_COURSE_IDS=set())
    def test_download_external_grades_csv(self):
        """
        Test with an external course--should return less stuff.
        """
        print "running test_download_grades_csv"
        toy = self.toy
        self.check_download_grades_csv(toy, toy.id in settings.INTERNAL_COURSE_IDS)

    def check_download_grades_csv(self, course, internal):
        print "checking course {0}".format(course.id)
        url = reverse('instructor_dashboard', kwargs={'course_id': course.id})
        msg = "url = %s\n" % url
        response = self.client.post(url, {'action': 'Download CSV of all student grades for this course',
                                          })
        msg += "instructor dashboard download csv grades: response = '%s'\n" % response

        self.assertEqual(response['Content-Type'],'text/csv',msg)

        cdisp = response['Content-Disposition']
        msg += "Content-Disposition = '%s'\n" % cdisp
        self.assertEqual(cdisp, 'attachment; filename=grades_{0}.csv'.format(course.id), msg)

        body = response.content.replace('\r','')
        msg += "body = '%s'\n" % body

        # if internal, expect some more info.
        extra1 = '"Full Name","edX email","External email",' if internal else ''
        extra2 = '"Fred Weasley","view2@test.com","",' if internal else ''

        # All the not-actually-in-the-course hw and labs come from the
        # default grading policy string in graders.py
        expected_body = '''"ID","Username",{0}"HW 01","HW 02","HW 03","HW 04","HW 05","HW 06","HW 07","HW 08","HW 09","HW 10","HW 11","HW 12","HW Avg","Lab 01","Lab 02","Lab 03","Lab 04","Lab 05","Lab 06","Lab 07","Lab 08","Lab 09","Lab 10","Lab 11","Lab 12","Lab Avg","Midterm","Final"
"2","u2",{1}"0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0.0","0.0"
'''.format(extra1, extra2)
        self.assertEqual(body, expected_body, msg)
