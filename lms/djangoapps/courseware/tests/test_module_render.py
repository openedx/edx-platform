from mock import Mock
from unittest import TestSuite

class TestStudentModule(TestSuite):
    def setUp(self):
        self.anon_user = Mock()
        self.anon_user.is_authenticated.return_value = True

    def anonymous_user(self):
        self.assert_equals(None, get_or_create_student_module('course_id', self.anon_user, None, None, None))