"""
Tests for instructor.basic
"""


from unittest.mock import MagicMock, Mock, patch

import ddt
import json  # lint-amnesty, pylint: disable=wrong-import-order
from edx_proctoring.api import create_exam
from edx_proctoring.models import ProctoredExamStudentAttempt
from opaque_keys.edx.locator import UsageKey
from lms.djangoapps.instructor_analytics.basic import (  # lint-amnesty, pylint: disable=unused-import
    AVAILABLE_FEATURES,
    PROFILE_FEATURES,
    PROGRAM_ENROLLMENT_FEATURES,
    STUDENT_FEATURES,
    StudentModule,
    enrolled_students_features,
    get_proctored_exam_results,
    get_response_state,
    list_may_enroll,
    list_problem_responses
)
from lms.djangoapps.program_enrollments.tests.factories import ProgramEnrollmentFactory
from openedx.core.djangoapps.course_groups.tests.helpers import CohortFactory
from common.djangoapps.student.models import CourseEnrollment, CourseEnrollmentAllowed
from common.djangoapps.student.tests.factories import InstructorFactory
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.tests.factories import CourseFactory  # lint-amnesty, pylint: disable=wrong-import-order


@ddt.ddt
class TestAnalyticsBasic(ModuleStoreTestCase):
    """ Test basic analytics functions. """

    def setUp(self):
        super().setUp()
        self.course_key = self.store.make_course_key('robot', 'course', 'id')
        self.users = tuple(UserFactory() for _ in range(30))
        self.ces = tuple(CourseEnrollment.enroll(user, self.course_key)
                         for user in self.users)
        self.instructor = InstructorFactory(course_key=self.course_key)
        for user in self.users:
            user.profile.meta = json.dumps({
                "position": f"edX expert {user.id}",
                "company": f"Open edX Inc {user.id}",
            })
            user.profile.save()
        self.students_who_may_enroll = list(self.users) + [UserFactory() for _ in range(5)]
        for student in self.students_who_may_enroll:
            CourseEnrollmentAllowed.objects.create(
                email=student.email,
                course_id=self.course_key,
                user=student if student in self.users else None,
            )

    @ddt.data(
        ('あなた', 'スの中'),
        ("ГЂіи lіиэ ъэтшээи", "Ђэаvэи аиↁ Ђэѓэ")
    )
    @ddt.unpack
    def test_get_response_state_with_ora(self, files_descriptions, saved_response):
        """
        Tests that ORA response state is transformed expectedly when the problem
        state contains unicode characters.
        """
        payload_state = json.dumps({
            'saved_response': json.dumps({'parts': [{'text': saved_response}]}),
            'saved_files_descriptions': json.dumps([files_descriptions]),
        })
        response = Mock(module_type='openassessment', student=Mock(username='staff'), state=payload_state)

        transformed_state = json.loads(get_response_state(response))
        assert transformed_state['saved_files_descriptions'][0] == files_descriptions
        assert transformed_state['saved_response']['parts'][0]['text'] == saved_response

    def test_list_problem_responses(self):
        def result_factory(result_id):
            """
            Return a dummy StudentModule object that can be queried for
            relevant info (student.username and state).
            """
            result = Mock(spec=['student', 'state'])
            result.student.username.return_value = f'user{result_id}'
            result.state.return_value = f'state{result_id}'
            return result

        # Ensure that UsageKey.from_string returns a problem key that list_problem_responses can work with
        # (even when called with a dummy location):
        mock_problem_key = Mock(return_value='')
        mock_problem_key.course_key = self.course_key
        with patch.object(UsageKey, 'from_string') as patched_from_string:
            patched_from_string.return_value = mock_problem_key

            # Ensure that StudentModule.objects.filter returns a result set that list_problem_responses can work with
            # (this keeps us from having to create fixtures for this test):
            mock_results = MagicMock(return_value=[result_factory(n) for n in range(5)])
            with patch.object(StudentModule, 'objects') as patched_manager:
                patched_manager.filter.return_value = mock_results

                mock_problem_location = ''
                problem_responses = list_problem_responses(self.course_key, problem_location=mock_problem_location)

                # Check if list_problem_responses called UsageKey.from_string to look up problem key:
                patched_from_string.assert_called_once_with(mock_problem_location)
                # Check if list_problem_responses called StudentModule.objects.filter to obtain relevant records:
                patched_manager.filter.assert_called_once_with(
                    course_id=self.course_key, module_state_key=mock_problem_key
                )

                # Check if list_problem_responses returned expected results:
                assert len(problem_responses) == len(mock_results)
                for mock_result in mock_results:
                    assert {'username': mock_result.student.username, 'state': mock_result.state} in problem_responses

    def test_enrolled_students_features_username(self):
        assert 'username' in AVAILABLE_FEATURES
        userreports = enrolled_students_features(self.course_key, ['username'])
        assert len(userreports) == len(self.users)
        for userreport in userreports:
            assert list(userreport.keys()) == ['username']
            assert userreport['username'] in [user.username for user in self.users]

    def test_enrolled_students_features_keys(self):
        query_features = ('username', 'name', 'email', 'city', 'country',)
        for user in self.users:
            user.profile.city = f"Mos Eisley {user.id}"
            user.profile.country = f"Tatooine {user.id}"
            user.profile.save()
        for feature in query_features:
            assert feature in AVAILABLE_FEATURES
        with self.assertNumQueries(1):
            userreports = enrolled_students_features(self.course_key, query_features)
        assert len(userreports) == len(self.users)

        userreports = sorted(userreports, key=lambda u: u["username"])
        users = sorted(self.users, key=lambda u: u.username)
        for userreport, user in zip(userreports, users):
            assert set(userreport.keys()) == set(query_features)
            assert userreport['username'] == user.username
            assert userreport['email'] == user.email
            assert userreport['name'] == user.profile.name
            assert userreport['city'] == user.profile.city
            assert userreport['country'] == user.profile.country

    def test_enrolled_student_with_no_country_city(self):
        userreports = enrolled_students_features(self.course_key, ('username', 'city', 'country',))
        for userreport in userreports:
            # This behaviour is somewhat inconsistent: None string fields
            # objects are converted to "None", but non-JSON serializable fields
            # are converted to an empty string.
            assert userreport['city'] == 'None'
            assert userreport['country'] == ''

    def test_enrolled_students_meta_features_keys(self):
        """
        Assert that we can query individual fields in the 'meta' field in the UserProfile
        """
        query_features = ('meta.position', 'meta.company')
        with self.assertNumQueries(1):
            userreports = enrolled_students_features(self.course_key, query_features)
        assert len(userreports) == len(self.users)
        for userreport in userreports:
            assert set(userreport.keys()) == set(query_features)
            assert userreport['meta.position'] in [f"edX expert {user.id}" for user in self.users]
            assert userreport['meta.company'] in [f"Open edX Inc {user.id}" for user in self.users]

    def test_enrolled_students_enrollment_verification(self):
        """
        Assert that we can get enrollment mode and verification status
        """
        query_features = ('enrollment_mode', 'verification_status')
        userreports = enrolled_students_features(self.course_key, query_features)
        assert len(userreports) == len(self.users)
        # by default all users should have "audit" as their enrollment mode
        # and "N/A" as their verification status
        for userreport in userreports:
            assert set(userreport.keys()) == set(query_features)
            assert userreport['enrollment_mode'] in ['audit']
            assert userreport['verification_status'] in ['N/A']
        # make sure that the user report respects whatever value
        # is returned by verification and enrollment code
        with patch("common.djangoapps.student.models.CourseEnrollment.enrollment_mode_for_user") as enrollment_patch:
            with patch(
                "lms.djangoapps.verify_student.services.IDVerificationService.verification_status_for_user"
            ) as verify_patch:
                enrollment_patch.return_value = ["verified"]
                verify_patch.return_value = "dummy verification status"
                userreports = enrolled_students_features(self.course_key, query_features)
                assert len(userreports) == len(self.users)
                for userreport in userreports:
                    assert set(userreport.keys()) == set(query_features)
                    assert userreport['enrollment_mode'] in ['verified']
                    assert userreport['verification_status'] in ['dummy verification status']

    def test_enrolled_students_features_keys_cohorted(self):
        course = CourseFactory.create(org="test", course="course1", display_name="run1")
        course.cohort_config = {'cohorted': True, 'auto_cohort': True, 'auto_cohort_groups': ['cohort']}
        self.store.update_item(course, self.instructor.id)
        cohorted_students = [UserFactory.create() for _ in range(10)]
        cohort = CohortFactory.create(name='cohort', course_id=course.id, users=cohorted_students)
        cohorted_usernames = [student.username for student in cohorted_students]
        non_cohorted_student = UserFactory.create()
        for student in cohorted_students:
            cohort.users.add(student)
            CourseEnrollment.enroll(student, course.id)
        CourseEnrollment.enroll(non_cohorted_student, course.id)
        instructor = InstructorFactory(course_key=course.id)
        self.client.login(username=instructor.username, password='test')

        query_features = ('username', 'cohort')
        # There should be a constant of 2 SQL queries when calling
        # enrolled_students_features.  The first query comes from the call to
        # User.objects.filter(...), and the second comes from
        # prefetch_related('course_groups').
        with self.assertNumQueries(2):
            userreports = enrolled_students_features(course.id, query_features)
        assert len([r for r in userreports if r['username'] in cohorted_usernames]) == len(cohorted_students)
        assert len([r for r in userreports if r['username'] == non_cohorted_student.username]) == 1
        for report in userreports:
            assert set(report.keys()) == set(query_features)
            if report['username'] in cohorted_usernames:
                assert report['cohort'] == cohort.name
            else:
                assert report['cohort'] == '[unassigned]'

    def test_enrolled_student_features_external_user_keys(self):
        query_features = ('username', 'name', 'email', 'city', 'country', 'external_user_key')
        username_with_external_user_key_dict = {}
        for i in range(len(self.users)):
            # Setup some users with ProgramEnrollments
            if i % 2 == 0:
                user = self.users[i]
                external_user_key = f'{user.username}_{i}'
                ProgramEnrollmentFactory.create(user=user, external_user_key=external_user_key)
                username_with_external_user_key_dict[user.username] = external_user_key

        with self.assertNumQueries(2):
            userreports = enrolled_students_features(self.course_key, query_features)
        assert len(userreports) == 30
        for report in userreports:
            username = report['username']
            external_key = username_with_external_user_key_dict.get(username)
            if external_key:
                assert external_key == report['external_user_key']
            else:
                assert '' == report['external_user_key']

    def test_available_features(self):
        assert len(AVAILABLE_FEATURES) == len(STUDENT_FEATURES + PROFILE_FEATURES + PROGRAM_ENROLLMENT_FEATURES)
        assert set(AVAILABLE_FEATURES) == set(STUDENT_FEATURES + PROFILE_FEATURES + PROGRAM_ENROLLMENT_FEATURES)

    def test_list_may_enroll(self):
        may_enroll = list_may_enroll(self.course_key, ['email'])
        assert len(may_enroll) == (len(self.students_who_may_enroll) - len(self.users))
        email_adresses = [student.email for student in self.students_who_may_enroll]
        for student in may_enroll:
            assert list(student.keys()) == ['email']
            assert student['email'] in email_adresses

    def test_get_student_exam_attempt_features(self):
        query_features = [
            'email',
            'exam_name',
            'allowed_time_limit_mins',
            'is_sample_attempt',
            'started_at',
            'completed_at',
            'status',
            'Suspicious Count',
            'Suspicious Comments',
            'Rules Violation Count',
            'Rules Violation Comments',
            'track'
        ]

        proctored_exam_id = create_exam(self.course_key, 'Test Content', 'Test Exam', 1)
        ProctoredExamStudentAttempt.create_exam_attempt(
            proctored_exam_id, self.users[0].id,
            'Test Code 1', True, False, 'ad13'
        )
        ProctoredExamStudentAttempt.create_exam_attempt(
            proctored_exam_id, self.users[1].id,
            'Test Code 2', True, False, 'ad13'
        )
        ProctoredExamStudentAttempt.create_exam_attempt(
            proctored_exam_id, self.users[2].id,
            'Test Code 3', True, False, 'asd'
        )

        proctored_exam_attempts = get_proctored_exam_results(self.course_key, query_features)
        assert len(proctored_exam_attempts) == 3
        for proctored_exam_attempt in proctored_exam_attempts:
            assert set(proctored_exam_attempt.keys()) == set(query_features)
