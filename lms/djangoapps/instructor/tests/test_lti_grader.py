"""
Tests for the Mgmt Commands Feature on the Sysadmin page
"""
import unittest
from mock import patch

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from dashboard.tests.test_sysadmin import SysadminBaseTestCase
from instructor.lti_grader import LTIGrader


@unittest.skipUnless(
    settings.FEATURES.get('ENABLE_SYSADMIN_DASHBOARD'),
    'ENABLE_SYSADMIN_DASHBOARD not set',
)
class TestLtiGrader(SysadminBaseTestCase):
    """Tests all code paths in Sysadmin Mgmt Commands"""

    def setUp(self):
        super(TestLtiGrader, self).setUp()
        self._setsuperuser_login()
        self.post_params = {
            'command': 'fake_command',
            'key1': 'value1',
            'key2': 'value2',
            'kwflags': ['kwflag1', 'kwflag2'],
            'args': ['arg1', 'arg2'],
        }
        self.data = SimpleUploadedFile(
            'file.csv',
            'ID,Anonymized User ID,email,grade, max_grade, comments,'
            '\n1,abcdabcd,abcd@abcd.com,5,10,not bad'
            '\n2,cdefcdef,cdef@cdef.com,6,10,great'
        )
        self.grader = LTIGrader('course_id', 'url_base', 'lti_key', 'lti_secret')

    def test_lti_grader_properly_initialized(self):
        self.assertEquals('course_id', self.grader.course_id)
        self.assertEquals('url_base', self.grader.url_base)
        self.assertEquals('lti_key', self.grader.key)
        self.assertEquals('lti_secret', self.grader.secret)

    def test_get_first_anon_id(self):
        first_anon_id = self.grader._get_first_anon_id(self.data)  # pylint: disable=protected-access
        self.assertEquals(first_anon_id, 'abcdabcd')

    def test_generate_valid_grading_rows(self):
        valid_rows = self.grader._generate_valid_grading_rows(self.data)  # pylint: disable=protected-access
        self.assertEquals((1, u'abcdabcd', u'abcd@abcd.com', 5.0, 10.0, u'not bad'), valid_rows.next())
        self.assertEquals((2, u'cdefcdef', u'cdef@cdef.com', 6.0, 10.0, u'great'), valid_rows.next())

    def test_update_grades_passport_failure(self):
        def validate_passport_side_effect(key, secret, test_url):  # pylint: disable=unused-argument
            """
            Side effect designed to replace validate_lti_passport in lti_connection.py, mocking validation failure
            """
            return False
        with patch('instructor.lti_grader.lti_connection') as mock_lti_connection:
            mock_lti_connection.validate_lti_passport.side_effect = validate_passport_side_effect
            actual_output = self.grader.update_grades(self.data)['error']
            expected_output = ['LTI passport sanity check failed. Your lti_key (lti_key) or lti_secret (lti_secret) are probably incorrect.']
            self.assertEquals(expected_output, actual_output)

    def test_update_grades_success(self):
        def validate_passport_side_effect(key, secret, test_url):  # pylint: disable=unused-argument
            """
            Side effect designed to replace validate_lti_passport in lti_connection.py, mocking validation success
            """
            return True

        def post_success_side_effect(url_base, key, secret, grade_row):  # pylint: disable=unused-argument
            """
            Side effect designed to replace post_grade in lti_connection.py, mocking successful grade post
            """
            return (True, grade_row[0], grade_row[2])
        with patch('instructor.lti_grader.lti_connection') as mock_lti_connection:
            mock_lti_connection.validate_lti_passport.side_effect = validate_passport_side_effect
            mock_lti_connection.post_grade.side_effect = post_success_side_effect
            actual_output = self.grader.update_grades(self.data)['success']
            expected_output = ['Grade post successful: user id 1 (email: abcd@abcd.com).', 'Grade post successful: user id 2 (email: cdef@cdef.com).']
            self.assertEquals(expected_output, actual_output)

    def test_update_grades_failure(self):
        def validate_passport_side_effect(key, secret, test_url):  # pylint: disable=unused-argument
            """
            Side effect designed to replace validate_lti_passport in lti_connection.py, mocking validation success
            """
            return True

        def post_failure_side_effect(url_base, key, secret, grade_row):  # pylint: disable=unused-argument
            """
            Side effect designed to replace post_grade in lti_connection.py, mocking unsuccessful grade post
            """
            return (False, grade_row[0], grade_row[2])
        with patch('instructor.lti_grader.lti_connection') as mock_lti_connection:
            mock_lti_connection.validate_lti_passport.side_effect = validate_passport_side_effect
            mock_lti_connection.post_grade.side_effect = post_failure_side_effect
            actual_output = self.grader.update_grades(self.data)['error']
            expected_output = ['Grade post failed: user id 1 (email: abcd@abcd.com).', 'Grade post failed: user id 2 (email: cdef@cdef.com).']
            self.assertEquals(expected_output, actual_output)
