"""
View-level tests for resetting student state in legacy instructor dash.
"""

import json
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from courseware.tests.helpers import LoginEnrollmentTestCase
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from courseware.tests.modulestore_config import TEST_DATA_MONGO_MODULESTORE
from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory, AdminFactory, CourseEnrollmentFactory

from courseware.models import StudentModule

from submissions import api as sub_api
from student.models import anonymous_id_for_user


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class InstructorResetStudentStateTest(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Reset student state from the legacy instructor dash.
    """

    def setUp(self):
        """
        Log in as an instructor, and create a course/student to reset.
        """
        instructor = AdminFactory.create()
        self.client.login(username=instructor.username, password='test')
        self.student = UserFactory.create(username='test', email='test@example.com')
        self.course = CourseFactory.create()
        CourseEnrollmentFactory.create(user=self.student, course_id=self.course.id)

    def test_delete_student_state_resets_scores(self):
        problem_location = self.course.id.make_usage_key('dummy', 'module')

        # Create a student module for the user
        StudentModule.objects.create(
            student=self.student,
            course_id=self.course.id,
            module_state_key=problem_location,
            state=json.dumps({})
        )

        # Create a submission and score for the student using the submissions API
        student_item = {
            'student_id': anonymous_id_for_user(self.student, self.course.id),
            'course_id': self.course.id.to_deprecated_string(),
            'item_id': problem_location.to_deprecated_string(),
            'item_type': 'openassessment'
        }
        submission = sub_api.create_submission(student_item, 'test answer')
        sub_api.set_score(submission['uuid'], 1, 2)

        # Delete student state using the instructor dash
        url = reverse('instructor_dashboard_legacy', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {
            'action': 'Delete student state for module',
            'unique_student_identifier': self.student.email,
            'problem_for_student': problem_location.to_deprecated_string(),
        })

        self.assertEqual(response.status_code, 200)

        # Verify that the student's scores have been reset in the submissions API
        score = sub_api.get_score(student_item)
        self.assertIs(score, None)
