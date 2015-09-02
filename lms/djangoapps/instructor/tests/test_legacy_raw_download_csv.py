# -*- coding: utf-8 -*-
"""
Create course and answer a problem to test raw grade CSV
"""

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from instructor.utils import DummyRequest
from instructor.views.legacy import get_student_grade_summary_data
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
        self.student_user2 = self.create_account('u2', self.instructor, self.password)
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

    def answer_question(self):
        """
        Answer a question correctly in the course
        """
        self.login(self.instructor, self.password)
        resp = self.submit_question_answer('p2', {'2_1': 'Correct'})
        self.assertEqual(resp.status_code, 200)

    def test_download_raw_grades_dump(self):
        """
        Grab raw grade report and make sure all grades are reported.
        """
        # Answer second problem correctly with 2nd user to expose bug
        self.answer_question()

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

    def test_grade_summary_data(self):
        """
        Test grade summary data report generation
        """
        self.answer_question()

        request = DummyRequest()
        data = get_student_grade_summary_data(request, self.course, get_raw_scores=False)
        expected_data = {
            'students': [self.student_user, self.student_user2],
            'header': [
                u'ID', u'Username', u'Full Name', u'edX email', u'External email',
                u'HW 01', u'HW 02', u'HW 03', u'HW 04', u'HW 05', u'HW 06', u'HW 07',
                u'HW 08', u'HW 09', u'HW 10', u'HW 11', u'HW 12', u'HW Avg', u'Lab 01',
                u'Lab 02', u'Lab 03', u'Lab 04', u'Lab 05', u'Lab 06', u'Lab 07',
                u'Lab 08', u'Lab 09', u'Lab 10', u'Lab 11', u'Lab 12', u'Lab Avg', u'Midterm',
                u'Final'
            ],
            'data': [
                [
                    1, u'u1', u'username', u'view@test.com', '', 0.0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
                ],
                [
                    2, u'u2', u'username', u'view2@test.com', '', 0.3333333333333333, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0.03333333333333333, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0
                ]
            ],
            'assignments': [
                u'HW 01', u'HW 02', u'HW 03', u'HW 04', u'HW 05', u'HW 06', u'HW 07', u'HW 08',
                u'HW 09', u'HW 10', u'HW 11', u'HW 12', u'HW Avg', u'Lab 01', u'Lab 02',
                u'Lab 03', u'Lab 04', u'Lab 05', u'Lab 06', u'Lab 07', u'Lab 08', u'Lab 09',
                u'Lab 10', u'Lab 11', u'Lab 12', u'Lab Avg', u'Midterm', u'Final'
            ]
        }

        for key in ['assignments', 'header']:
            self.assertListEqual(expected_data[key], data[key])

        for index, student in enumerate(expected_data['students']):
            self.assertEqual(
                student.username,
                data['students'][index].username
            )
            self.assertListEqual(
                expected_data['data'][index],
                data['data'][index]
            )
