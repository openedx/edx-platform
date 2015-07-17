# -*- coding: utf-8 -*-
"""
Create course and answer a problem to test raw grade CSV
"""

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from nose.plugins.attrib import attr

from courseware.tests.test_submitting_problems import TestSubmittingProblems
from student.roles import CourseStaffRole


@attr('shard_1')
class TestRawGradeCSV(TestSubmittingProblems):
    """
    Tests around the instructor dashboard raw grade CSV
    """

    def setUp(self):
        """
        Set up a simple course for testing basic grading functionality.
        """
        super(TestRawGradeCSV, self).setUp()

        self.instructor = 'view2@test.com'
        self.create_account('u2', self.instructor, self.password)
        self.activate_user(self.instructor)
        CourseStaffRole(self.course.id).add_users(User.objects.get(email=self.instructor))
        self.logout()
        self.login(self.instructor, self.password)
        self.enroll(self.course)

        # set up a simple course with four problems
        self.homework = self.add_graded_section_to_course('homework', late=False, reset=False, showanswer=False)
        self.add_dropdown_to_section(self.homework.location, 'p1', 1)
        self.add_dropdown_to_section(self.homework.location, 'p2', 1)
        self.add_dropdown_to_section(self.homework.location, 'p3', 1)
        self.refresh_course()

    def test_download_raw_grades_dump(self):
        """
        Grab raw grade report and make sure all grades are reported.
        """
        # Answer second problem correctly with 2nd user to expose bug
        self.login(self.instructor, self.password)
        resp = self.submit_question_answer('p2', {'2_1': 'Correct'})
        self.assertEqual(resp.status_code, 200)

        url = reverse('instructor_dashboard_legacy', kwargs={'course_id': self.course.id.to_deprecated_string()})
        msg = "url = {0}\n".format(url)
        response = self.client.post(url, {'action': 'Download CSV of all RAW grades'})
        msg += "instructor dashboard download raw csv grades: response = '{0}'\n".format(response)
        body = response.content.replace('\r', '')
        msg += "body = '{0}'\n".format(body)
        expected_csv = '''"ID","Username","Full Name","edX email","External email","p3","p2","p1"
"1","u1","username","view@test.com","","None","None","None"
"2","u2","username","view2@test.com","","0.0","1.0","0.0"
'''
        self.assertEqual(body, expected_csv, msg)
