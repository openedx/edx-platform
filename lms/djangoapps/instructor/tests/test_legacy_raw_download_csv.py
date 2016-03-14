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

    def get_expected_grade_data(
            self, get_grades=True, get_raw_scores=False,
            use_offline=False, get_score_max=False):
        """
        Return expected results from the get_student_grade_summary_data call
        with any options selected.

        Note that the kwargs accepted by get_expected_grade_data (and their
        default values) must be identical to those in
        get_student_grade_summary_data for this function to be accurate.
        If kwargs are added or removed, or the functionality triggered by
        them changes, this function must be updated to match.

        If get_score_max is True, instead of a single score between 0 and 1,
        the actual score and total possible are returned. For example, if the
        student got one out of two possible points, the values (1, 2) will be
        returned instead of 0.5.
        """
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

        # The first five columns contain the student ID, username,
        # full name, and e-mail addresses.
        non_grade_columns = 5
        # If the following 'if' is triggered, the
        # get_student_grade_summary_data function will not return any
        # grade data. Only the "non_grade_columns."
        # So strip out the headers beyond the "non_grade_columns," and
        # strip out all the grades in the 'data' key.
        if not get_grades or use_offline:
            expected_data["header"] = expected_data["header"][:non_grade_columns]
            # This iterates over the lists of grades in the 'data' key
            # of the return dictionary and strips out everything after
            # the non_grade_columns.
            for index, rec in enumerate(expected_data["data"]):
                expected_data["data"][index] = rec[:non_grade_columns]
            # Wipe out all data in the 'assignments' key if use_offline
            # is True; no assignment data is returned.
            if use_offline:
                expected_data['assignments'] = []
            # If get_grades is False, get_student_grade_summary_data doesn't
            # even return an 'assignments' key, so delete it.
            if get_grades is False:
                del expected_data['assignments']
        # If get_raw_scores is true, get_student_grade_summary_data returns
        # the raw score per assignment. For example, the "0.3333333333333333"
        # in the data above is for getting one out of three possible
        # answers correct. Getting raw scores means the actual score (1) is
        # return instead of: 1.0/3.0
        # For some reason, this also causes it to not to return any assignments
        # without attempts, so most of the headers are removed.
        elif get_raw_scores:
            expected_data["data"] = [
                [
                    1, u'u1', u'username', u'view@test.com',
                    '', None, None, None
                ],
                [
                    2, u'u2', u'username', u'view2@test.com',
                    '', 0.0, 1.0, 0.0
                ],
            ]
            expected_data["assignments"] = [u'p3', u'p2', u'p1']
            expected_data["header"] = [
                u'ID', u'Username', u'Full Name', u'edX email',
                u'External email', u'p3', u'p2', u'p1'
            ]
            # Strip out the single-value float scores and replace them
            # with two-tuples of actual and possible scores (see docstring).
            if get_score_max:
                expected_data["data"][-1][-3:] = (0.0, 1), (1.0, 1.0), (0.0, 1)

        return expected_data

    def test_grade_summary_data_defaults(self):
        """
        Test grade summary data report generation with all default kwargs.

        This test compares the output of the get_student_grade_summary_data
        with a dictionary of exected values. The purpose of this test is
        to ensure that future changes to the get_student_grade_summary_data
        function (for example, mitocw/edx-platform #95).
        """
        request = DummyRequest()
        self.answer_question()
        data = get_student_grade_summary_data(request, self.course)
        expected_data = self.get_expected_grade_data()
        self.compare_data(data, expected_data)

    def test_grade_summary_data_raw_scores(self):
        """
        Test grade summary data report generation with get_raw_scores True.
        """
        request = DummyRequest()
        self.answer_question()
        data = get_student_grade_summary_data(
            request, self.course, get_raw_scores=True,
        )
        expected_data = self.get_expected_grade_data(get_raw_scores=True)
        self.compare_data(data, expected_data)

    def test_grade_summary_data_no_grades(self):
        """
        Test grade summary data report generation with
        get_grades set to False.
        """
        request = DummyRequest()
        self.answer_question()

        data = get_student_grade_summary_data(
            request, self.course, get_grades=False
        )
        expected_data = self.get_expected_grade_data(get_grades=False)
        # if get_grades is False, get_expected_grade_data does not
        # add an "assignments" key.
        self.assertNotIn("assignments", expected_data)
        self.compare_data(data, expected_data)

    def test_grade_summary_data_use_offline(self):
        """
        Test grade summary data report generation with use_offline True.
        """
        request = DummyRequest()
        self.answer_question()
        data = get_student_grade_summary_data(
            request, self.course, use_offline=True)
        expected_data = self.get_expected_grade_data(use_offline=True)
        self.compare_data(data, expected_data)

    def test_grade_summary_data_use_offline_and_raw_scores(self):
        """
        Test grade summary data report generation with use_offline
        and get_raw_scores both True.
        """
        request = DummyRequest()
        self.answer_question()
        data = get_student_grade_summary_data(
            request, self.course, use_offline=True, get_raw_scores=True
        )
        expected_data = self.get_expected_grade_data(
            use_offline=True, get_raw_scores=True
        )
        self.compare_data(data, expected_data)

    def test_grade_summary_data_get_score_max(self):
        """
        Test grade summary data report generation with get_score_max set
        to True (also requires get_raw_scores to be True).
        """
        request = DummyRequest()
        self.answer_question()
        data = get_student_grade_summary_data(
            request, self.course, use_offline=True, get_raw_scores=True,
            get_score_max=True,
        )
        expected_data = self.get_expected_grade_data(
            use_offline=True, get_raw_scores=True, get_score_max=True,
        )
        self.compare_data(data, expected_data)

    def compare_data(self, data, expected_data):
        """
        Compare the output of the get_student_grade_summary_data
        function to the expected_data data.
        """

        # Currently, all kwargs to get_student_grade_summary_data
        # return a dictionary with the same keys, except for
        # get_grades=False, which results in no 'assignments' key.
        # This is explicitly checked for above in
        # test_grade_summary_data_no_grades. This is a backup which
        # will catch future changes.
        self.assertListEqual(
            expected_data.keys(),
            data.keys(),
        )

        # Ensure the student info and assignment names are as expected.
        for key in ['assignments', 'header']:
            self.assertListEqual(
                expected_data.get(key, []),
                data.get(key, []),
            )

        # Ensure each student's grades are as expected for each assignment.
        for index, student in enumerate(expected_data['students']):
            self.assertEqual(
                student.username,
                data['students'][index].username
            )
            self.assertListEqual(
                expected_data['data'][index],
                data['data'][index]
            )
