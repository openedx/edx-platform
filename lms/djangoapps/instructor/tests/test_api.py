"""
Unit tests for instructor.api methods.
"""
# pylint: disable=E1111
import unittest
import json
import requests
from urllib import quote
from django.conf import settings
from django.test import TestCase
from nose.tools import raises
from mock import Mock, patch
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.http import HttpRequest, HttpResponse

from django.contrib.auth.models import User
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from courseware.tests.helpers import LoginEnrollmentTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory, AdminFactory

from student.models import CourseEnrollment
from courseware.models import StudentModule

# modules which are mocked in test cases.
import instructor_task.api

from instructor.access import allow_access
import instructor.views.api
from instructor.views.api import (
    _split_input_list, _msk_from_problem_urlname, common_exceptions_400)
from instructor_task.api_helper import AlreadyRunningError


@common_exceptions_400
def view_success(request):  # pylint: disable=W0613
    "A dummy view for testing that returns a simple HTTP response"
    return HttpResponse('success')


@common_exceptions_400
def view_user_doesnotexist(request):  # pylint: disable=W0613
    "A dummy view that raises a User.DoesNotExist exception"
    raise User.DoesNotExist()


@common_exceptions_400
def view_alreadyrunningerror(request):  # pylint: disable=W0613
    "A dummy view that raises an AlreadyRunningError exception"
    raise AlreadyRunningError()


class TestCommonExceptions400(unittest.TestCase):
    """
    Testing the common_exceptions_400 decorator.
    """
    def setUp(self):
        self.request = Mock(spec=HttpRequest)
        self.request.META = {}

    def test_happy_path(self):
        resp = view_success(self.request)
        self.assertEqual(resp.status_code, 200)

    def test_user_doesnotexist(self):
        self.request.is_ajax.return_value = False
        resp = view_user_doesnotexist(self.request)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("User does not exist", resp.content)

    def test_user_doesnotexist_ajax(self):
        self.request.is_ajax.return_value = True
        resp = view_user_doesnotexist(self.request)
        self.assertEqual(resp.status_code, 400)
        result = json.loads(resp.content)
        self.assertIn("User does not exist", result["error"])

    def test_alreadyrunningerror(self):
        self.request.is_ajax.return_value = False
        resp = view_alreadyrunningerror(self.request)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Task is already running", resp.content)

    def test_alreadyrunningerror_ajax(self):
        self.request.is_ajax.return_value = True
        resp = view_alreadyrunningerror(self.request)
        self.assertEqual(resp.status_code, 400)
        result = json.loads(resp.content)
        self.assertIn("Task is already running", result["error"])


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestInstructorAPIDenyLevels(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Ensure that users cannot access endpoints they shouldn't be able to.
    """
    def setUp(self):
        self.user = UserFactory.create()
        self.course = CourseFactory.create()
        CourseEnrollment.enroll(self.user, self.course.id)
        self.client.login(username=self.user.username, password='test')

    def test_deny_students_update_enrollment(self):
        url = reverse('students_update_enrollment', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {})
        self.assertEqual(response.status_code, 403)

    def test_staff_level(self):
        """
        Ensure that an enrolled student can't access staff or instructor endpoints.
        """
        staff_level_endpoints = [
            'students_update_enrollment',
            'modify_access',
            'list_course_role_members',
            'get_grading_config',
            'get_students_features',
            'get_distribution',
            'get_student_progress_url',
            'reset_student_attempts',
            'rescore_problem',
            'list_instructor_tasks',
            'list_forum_members',
            'update_forum_role_membership',
            'proxy_legacy_analytics',
        ]
        for endpoint in staff_level_endpoints:
            url = reverse(endpoint, kwargs={'course_id': self.course.id})
            response = self.client.get(url, {})
            self.assertEqual(response.status_code, 403)

    def test_instructor_level(self):
        """
        Ensure that a staff member can't access instructor endpoints.
        """
        instructor_level_endpoints = [
            'modify_access',
            'list_course_role_members',
            'reset_student_attempts',
            'list_instructor_tasks',
            'update_forum_role_membership',
        ]
        for endpoint in instructor_level_endpoints:
            url = reverse(endpoint, kwargs={'course_id': self.course.id})
            response = self.client.get(url, {})
            self.assertEqual(response.status_code, 403)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestInstructorAPIEnrollment(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test enrollment modification endpoint.

    This test does NOT exhaustively test state changes, that is the
    job of test_enrollment. This tests the response and action switch.
    """
    def setUp(self):
        self.instructor = AdminFactory.create()
        self.course = CourseFactory.create()
        self.client.login(username=self.instructor.username, password='test')

        self.enrolled_student = UserFactory()
        CourseEnrollment.enroll(
            self.enrolled_student,
            self.course.id
        )
        self.notenrolled_student = UserFactory()

        self.notregistered_email = 'robot-not-an-email-yet@robot.org'
        self.assertEqual(User.objects.filter(email=self.notregistered_email).count(), 0)

        # uncomment to enable enable printing of large diffs
        # from failed assertions in the event of a test failure.
        # (comment because pylint C0103)
        # self.maxDiff = None

    def test_missing_params(self):
        """ Test missing all query parameters. """
        url = reverse('students_update_enrollment', kwargs={'course_id': self.course.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_bad_action(self):
        """ Test with an invalid action. """
        action = 'robot-not-an-action'
        url = reverse('students_update_enrollment', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {'emails': self.enrolled_student.email, 'action': action})
        self.assertEqual(response.status_code, 400)

    def test_enroll(self):
        url = reverse('students_update_enrollment', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {'emails': self.notenrolled_student.email, 'action': 'enroll'})
        print "type(self.notenrolled_student.email): {}".format(type(self.notenrolled_student.email))
        self.assertEqual(response.status_code, 200)
        # test that the user is now enrolled

        self.assertEqual(
            self.notenrolled_student.courseenrollment_set.filter(
                course_id=self.course.id
            ).count(),
            1
        )

        # test the response data
        expected = {
            "action": "enroll",
            "auto_enroll": False,
            "results": [
                {
                    "email": self.notenrolled_student.email,
                    "before": {
                        "enrollment": False,
                        "auto_enroll": False,
                        "user": True,
                        "allowed": False,
                    },
                    "after": {
                        "enrollment": True,
                        "auto_enroll": False,
                        "user": True,
                        "allowed": False,
                    }
                }
            ]
        }

        res_json = json.loads(response.content)
        self.assertEqual(res_json, expected)

    def test_unenroll(self):
        url = reverse('students_update_enrollment', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {'emails': self.enrolled_student.email, 'action': 'unenroll'})
        print "type(self.enrolled_student.email): {}".format(type(self.enrolled_student.email))
        self.assertEqual(response.status_code, 200)
        # test that the user is now unenrolled

        self.assertEqual(
            self.enrolled_student.courseenrollment_set.filter(
                course_id=self.course.id,
                is_active=1,
            ).count(),
            0
        )

        # test the response data
        expected = {
            "action": "unenroll",
            "auto_enroll": False,
            "results": [
                {
                    "email": self.enrolled_student.email,
                    "before": {
                        "enrollment": True,
                        "auto_enroll": False,
                        "user": True,
                        "allowed": False,
                    },
                    "after": {
                        "enrollment": False,
                        "auto_enroll": False,
                        "user": True,
                        "allowed": False,
                    }
                }
            ]
        }

        res_json = json.loads(response.content)
        self.assertEqual(res_json, expected)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestInstructorAPILevelsAccess(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test endpoints whereby instructors can change permissions
    of other users.

    This test does NOT test whether the actions had an effect on the
    database, that is the job of test_access.
    This tests the response and action switch.
    Actually, modify_access does not having a very meaningful
        response yet, so only the status code is tested.
    """
    def setUp(self):
        self.instructor = AdminFactory.create()
        self.course = CourseFactory.create()
        self.client.login(username=self.instructor.username, password='test')

        self.other_instructor = UserFactory()
        allow_access(self.course, self.other_instructor, 'instructor')
        self.other_staff = UserFactory()
        allow_access(self.course, self.other_staff, 'staff')
        self.other_user = UserFactory()

    def test_modify_access_noparams(self):
        """ Test missing all query parameters. """
        url = reverse('modify_access', kwargs={'course_id': self.course.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_modify_access_bad_action(self):
        """ Test with an invalid action parameter. """
        url = reverse('modify_access', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {
            'email': self.other_staff.email,
            'rolename': 'staff',
            'action': 'robot-not-an-action',
        })
        self.assertEqual(response.status_code, 400)

    def test_modify_access_bad_role(self):
        """ Test with an invalid action parameter. """
        url = reverse('modify_access', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {
            'email': self.other_staff.email,
            'rolename': 'robot-not-a-roll',
            'action': 'revoke',
        })
        self.assertEqual(response.status_code, 400)

    def test_modify_access_allow(self):
        url = reverse('modify_access', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {
            'email': self.other_instructor.email,
            'rolename': 'staff',
            'action': 'allow',
        })
        self.assertEqual(response.status_code, 200)

    def test_modify_access_revoke(self):
        url = reverse('modify_access', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {
            'email': self.other_staff.email,
            'rolename': 'staff',
            'action': 'revoke',
        })
        self.assertEqual(response.status_code, 200)

    def test_modify_access_revoke_not_allowed(self):
        """ Test revoking access that a user does not have. """
        url = reverse('modify_access', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {
            'email': self.other_staff.email,
            'rolename': 'instructor',
            'action': 'revoke',
        })
        self.assertEqual(response.status_code, 200)

    def test_modify_access_revoke_self(self):
        """
        Test that an instructor cannot remove instructor privelages from themself.
        """
        url = reverse('modify_access', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {
            'email': self.instructor.email,
            'rolename': 'instructor',
            'action': 'revoke',
        })
        self.assertEqual(response.status_code, 400)

    def test_list_course_role_members_noparams(self):
        """ Test missing all query parameters. """
        url = reverse('list_course_role_members', kwargs={'course_id': self.course.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_list_course_role_members_bad_rolename(self):
        """ Test with an invalid rolename parameter. """
        url = reverse('list_course_role_members', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {
            'rolename': 'robot-not-a-rolename',
        })
        print response
        self.assertEqual(response.status_code, 400)

    def test_list_course_role_members_staff(self):
        url = reverse('list_course_role_members', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {
            'rolename': 'staff',
        })
        print response
        self.assertEqual(response.status_code, 200)

        # check response content
        expected = {
            'course_id': self.course.id,
            'staff': [
                {
                    'username': self.other_staff.username,
                    'email': self.other_staff.email,
                    'first_name': self.other_staff.first_name,
                    'last_name': self.other_staff.last_name,
                }
            ]
        }
        res_json = json.loads(response.content)
        self.assertEqual(res_json, expected)

    def test_list_course_role_members_beta(self):
        url = reverse('list_course_role_members', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {
            'rolename': 'beta',
        })
        print response
        self.assertEqual(response.status_code, 200)

        # check response content
        expected = {
            'course_id': self.course.id,
            'beta': []
        }
        res_json = json.loads(response.content)
        self.assertEqual(res_json, expected)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestInstructorAPILevelsDataDump(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test endpoints that show data without side effects.
    """
    def setUp(self):
        self.instructor = AdminFactory.create()
        self.course = CourseFactory.create()
        self.client.login(username=self.instructor.username, password='test')

        self.students = [UserFactory() for _ in xrange(6)]
        for student in self.students:
            CourseEnrollment.enroll(student, self.course.id)

    def test_get_students_features(self):
        """
        Test that some minimum of information is formatted
        correctly in the response to get_students_features.
        """
        url = reverse('get_students_features', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {})
        res_json = json.loads(response.content)
        self.assertIn('students', res_json)
        for student in self.students:
            student_json = [
                x for x in res_json['students']
                if x['username'] == student.username
            ][0]
            self.assertEqual(student_json['username'], student.username)
            self.assertEqual(student_json['email'], student.email)

    def test_get_anon_ids(self):
        """
        Test the CSV output for the anonymized user ids.
        """
        url = reverse('get_anon_ids', kwargs={'course_id': self.course.id})
        with patch('instructor.views.api.unique_id_for_user') as mock_unique:
            mock_unique.return_value = '42'
            response = self.client.get(url, {})
        self.assertEqual(response['Content-Type'], 'text/csv')
        body = response.content.replace('\r', '')
        self.assertTrue(body.startswith('"User ID","Anonymized user ID"\n"2","42"\n'))
        self.assertTrue(body.endswith('"7","42"\n'))

    def test_get_students_features_csv(self):
        """
        Test that some minimum of information is formatted
        correctly in the response to get_students_features.
        """
        url = reverse('get_students_features', kwargs={'course_id': self.course.id})
        response = self.client.get(url + '/csv', {})
        self.assertEqual(response['Content-Type'], 'text/csv')

    def test_get_distribution_no_feature(self):
        """
        Test that get_distribution lists available features
        when supplied no feature quparameter.
        """
        url = reverse('get_distribution', kwargs={'course_id': self.course.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertEqual(type(res_json['available_features']), list)

        url = reverse('get_distribution', kwargs={'course_id': self.course.id})
        response = self.client.get(url + u'?feature=')
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertEqual(type(res_json['available_features']), list)

    def test_get_distribution_unavailable_feature(self):
        """
        Test that get_distribution fails gracefully with
            an unavailable feature.
        """
        url = reverse('get_distribution', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {'feature': 'robot-not-a-real-feature'})
        self.assertEqual(response.status_code, 400)

    def test_get_distribution_gender(self):
        """
        Test that get_distribution fails gracefully with
            an unavailable feature.
        """
        url = reverse('get_distribution', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {'feature': 'gender'})
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        print res_json
        self.assertEqual(res_json['feature_results']['data']['m'], 6)
        self.assertEqual(res_json['feature_results']['choices_display_names']['m'], 'Male')
        self.assertEqual(res_json['feature_results']['data']['no_data'], 0)
        self.assertEqual(res_json['feature_results']['choices_display_names']['no_data'], 'No Data')

    def test_get_student_progress_url(self):
        """ Test that progress_url is in the successful response. """
        url = reverse('get_student_progress_url', kwargs={'course_id': self.course.id})
        url += "?unique_student_identifier={}".format(
            quote(self.students[0].email.encode("utf-8"))
        )
        print url
        response = self.client.get(url)
        print response
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertIn('progress_url', res_json)

    def test_get_student_progress_url_from_uname(self):
        """ Test that progress_url is in the successful response. """
        url = reverse('get_student_progress_url', kwargs={'course_id': self.course.id})
        url += "?unique_student_identifier={}".format(
            quote(self.students[0].username.encode("utf-8"))
        )
        print url
        response = self.client.get(url)
        print response
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertIn('progress_url', res_json)

    def test_get_student_progress_url_noparams(self):
        """ Test that the endpoint 404's without the required query params. """
        url = reverse('get_student_progress_url', kwargs={'course_id': self.course.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_get_student_progress_url_nostudent(self):
        """ Test that the endpoint 400's when requesting an unknown email. """
        url = reverse('get_student_progress_url', kwargs={'course_id': self.course.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestInstructorAPIRegradeTask(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test endpoints whereby instructors can change student grades.
    This includes resetting attempts and starting rescore tasks.

    This test does NOT test whether the actions had an effect on the
    database, that is the job of task tests and test_enrollment.
    """
    def setUp(self):
        self.instructor = AdminFactory.create()
        self.course = CourseFactory.create()
        self.client.login(username=self.instructor.username, password='test')

        self.student = UserFactory()
        CourseEnrollment.enroll(self.student, self.course.id)

        self.problem_urlname = 'robot-some-problem-urlname'
        self.module_to_reset = StudentModule.objects.create(
            student=self.student,
            course_id=self.course.id,
            module_state_key=_msk_from_problem_urlname(
                self.course.id,
                self.problem_urlname
            ),
            state=json.dumps({'attempts': 10}),
        )

    def test_reset_student_attempts_deletall(self):
        """ Make sure no one can delete all students state on a problem. """
        url = reverse('reset_student_attempts', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {
            'problem_to_reset': self.problem_urlname,
            'all_students': True,
            'delete_module': True,
        })
        print response.content
        self.assertEqual(response.status_code, 400)

    def test_reset_student_attempts_single(self):
        """ Test reset single student attempts. """
        url = reverse('reset_student_attempts', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {
            'problem_to_reset': self.problem_urlname,
            'unique_student_identifier': self.student.email,
        })
        print response.content
        self.assertEqual(response.status_code, 200)
        # make sure problem attempts have been reset.
        changed_module = StudentModule.objects.get(pk=self.module_to_reset.pk)
        self.assertEqual(
            json.loads(changed_module.state)['attempts'],
            0
        )

    # mock out the function which should be called to execute the action.
    @patch.object(instructor_task.api, 'submit_reset_problem_attempts_for_all_students')
    def test_reset_student_attempts_all(self, act):
        """ Test reset all student attempts. """
        url = reverse('reset_student_attempts', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {
            'problem_to_reset': self.problem_urlname,
            'all_students': True,
        })
        print response.content
        self.assertEqual(response.status_code, 200)
        self.assertTrue(act.called)

    def test_reset_student_attempts_missingmodule(self):
        """ Test reset for non-existant problem. """
        url = reverse('reset_student_attempts', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {
            'problem_to_reset': 'robot-not-a-real-module',
            'unique_student_identifier': self.student.email,
        })
        print response.content
        self.assertEqual(response.status_code, 400)

    def test_reset_student_attempts_delete(self):
        """ Test delete single student state. """
        url = reverse('reset_student_attempts', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {
            'problem_to_reset': self.problem_urlname,
            'unique_student_identifier': self.student.email,
            'delete_module': True,
        })
        print response.content
        self.assertEqual(response.status_code, 200)
        # make sure the module has been deleted
        self.assertEqual(
            StudentModule.objects.filter(
                student=self.module_to_reset.student,
                course_id=self.module_to_reset.course_id,
                # module_state_key=self.module_to_reset.module_state_key,
            ).count(),
            0
        )

    def test_reset_student_attempts_nonsense(self):
        """ Test failure with both unique_student_identifier and all_students. """
        url = reverse('reset_student_attempts', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {
            'problem_to_reset': self.problem_urlname,
            'unique_student_identifier': self.student.email,
            'all_students': True,
        })
        print response.content
        self.assertEqual(response.status_code, 400)

    @patch.object(instructor_task.api, 'submit_rescore_problem_for_student')
    def test_rescore_problem_single(self, act):
        """ Test rescoring of a single student. """
        url = reverse('rescore_problem', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {
            'problem_to_reset': self.problem_urlname,
            'unique_student_identifier': self.student.email,
        })
        print response.content
        self.assertEqual(response.status_code, 200)
        self.assertTrue(act.called)

    @patch.object(instructor_task.api, 'submit_rescore_problem_for_student')
    def test_rescore_problem_single_from_uname(self, act):
        """ Test rescoring of a single student. """
        url = reverse('rescore_problem', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {
            'problem_to_reset': self.problem_urlname,
            'unique_student_identifier': self.student.username,
        })
        print response.content
        self.assertEqual(response.status_code, 200)
        self.assertTrue(act.called)

    @patch.object(instructor_task.api, 'submit_rescore_problem_for_all_students')
    def test_rescore_problem_all(self, act):
        """ Test rescoring for all students. """
        url = reverse('rescore_problem', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {
            'problem_to_reset': self.problem_urlname,
            'all_students': True,
        })
        print response.content
        self.assertEqual(response.status_code, 200)
        self.assertTrue(act.called)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestInstructorAPITaskLists(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test instructor task list endpoint.
    """

    class FakeTask(object):
        """ Fake task object """
        FEATURES = ['task_type', 'task_input', 'task_id', 'requester', 'created', 'task_state']

        def __init__(self):
            for feature in self.FEATURES:
                setattr(self, feature, 'expected')

        def to_dict(self):
            """ Convert fake task to dictionary representation. """
            return {key: 'expected' for key in self.FEATURES}

    def setUp(self):
        self.instructor = AdminFactory.create()
        self.course = CourseFactory.create()
        self.client.login(username=self.instructor.username, password='test')

        self.student = UserFactory()
        CourseEnrollment.enroll(self.student, self.course.id)

        self.problem_urlname = 'robot-some-problem-urlname'
        self.module = StudentModule.objects.create(
            student=self.student,
            course_id=self.course.id,
            module_state_key=_msk_from_problem_urlname(
                self.course.id,
                self.problem_urlname
            ),
            state=json.dumps({'attempts': 10}),
        )

        self.tasks = [self.FakeTask() for _ in xrange(6)]

    @patch.object(instructor_task.api, 'get_running_instructor_tasks')
    def test_list_instructor_tasks_running(self, act):
        """ Test list of all running tasks. """
        act.return_value = self.tasks
        url = reverse('list_instructor_tasks', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {})
        print response.content
        self.assertEqual(response.status_code, 200)

        # check response
        self.assertTrue(act.called)
        expected_tasks = [ftask.to_dict() for ftask in self.tasks]
        expected_res = {'tasks': expected_tasks}
        self.assertEqual(json.loads(response.content), expected_res)

    @patch.object(instructor_task.api, 'get_instructor_task_history')
    def test_list_instructor_tasks_problem(self, act):
        """ Test list task history for problem. """
        act.return_value = self.tasks
        url = reverse('list_instructor_tasks', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {
            'problem_urlname': self.problem_urlname,
        })
        print response.content
        self.assertEqual(response.status_code, 200)

        # check response
        self.assertTrue(act.called)
        expected_tasks = [ftask.to_dict() for ftask in self.tasks]
        expected_res = {'tasks': expected_tasks}
        self.assertEqual(json.loads(response.content), expected_res)

    @patch.object(instructor_task.api, 'get_instructor_task_history')
    def test_list_instructor_tasks_problem_student(self, act):
        """ Test list task history for problem AND student. """
        act.return_value = self.tasks
        url = reverse('list_instructor_tasks', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {
            'problem_urlname': self.problem_urlname,
            'unique_student_identifier': self.student.email,
        })
        print response.content
        self.assertEqual(response.status_code, 200)

        # check response
        self.assertTrue(act.called)
        expected_tasks = [ftask.to_dict() for ftask in self.tasks]
        expected_res = {'tasks': expected_tasks}
        self.assertEqual(json.loads(response.content), expected_res)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
@override_settings(ANALYTICS_SERVER_URL="http://robotanalyticsserver.netbot:900/")
@override_settings(ANALYTICS_API_KEY="robot_api_key")
class TestInstructorAPIAnalyticsProxy(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test instructor analytics proxy endpoint.
    """

    class FakeProxyResponse(object):
        """ Fake successful requests response object. """
        def __init__(self):
            self.status_code = requests.status_codes.codes.OK
            self.content = '{"test_content": "robot test content"}'

    class FakeBadProxyResponse(object):
        """ Fake strange-failed requests response object. """
        def __init__(self):
            self.status_code = 'notok.'
            self.content = '{"test_content": "robot test content"}'

    def setUp(self):
        self.instructor = AdminFactory.create()
        self.course = CourseFactory.create()
        self.client.login(username=self.instructor.username, password='test')

    @patch.object(instructor.views.api.requests, 'get')
    def test_analytics_proxy_url(self, act):
        """ Test legacy analytics proxy url generation. """
        act.return_value = self.FakeProxyResponse()

        url = reverse('proxy_legacy_analytics', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {
            'aname': 'ProblemGradeDistribution'
        })
        print response.content
        self.assertEqual(response.status_code, 200)

        # check request url
        expected_url = "{url}get?aname={aname}&course_id={course_id}&apikey={api_key}".format(
            url="http://robotanalyticsserver.netbot:900/",
            aname="ProblemGradeDistribution",
            course_id=self.course.id,
            api_key="robot_api_key",
        )
        act.assert_called_once_with(expected_url)

    @patch.object(instructor.views.api.requests, 'get')
    def test_analytics_proxy(self, act):
        """
        Test legacy analytics content proxyin, actg.
        """
        act.return_value = self.FakeProxyResponse()

        url = reverse('proxy_legacy_analytics', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {
            'aname': 'ProblemGradeDistribution'
        })
        print response.content
        self.assertEqual(response.status_code, 200)

        # check response
        self.assertTrue(act.called)
        expected_res = {'test_content': "robot test content"}
        self.assertEqual(json.loads(response.content), expected_res)

    @patch.object(instructor.views.api.requests, 'get')
    def test_analytics_proxy_reqfailed(self, act):
        """ Test proxy when server reponds with failure. """
        act.return_value = self.FakeBadProxyResponse()

        url = reverse('proxy_legacy_analytics', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {
            'aname': 'ProblemGradeDistribution'
        })
        print response.content
        self.assertEqual(response.status_code, 500)

    @patch.object(instructor.views.api.requests, 'get')
    def test_analytics_proxy_missing_param(self, act):
        """ Test proxy when missing the aname query parameter. """
        act.return_value = self.FakeProxyResponse()

        url = reverse('proxy_legacy_analytics', kwargs={'course_id': self.course.id})
        response = self.client.get(url, {})
        print response.content
        self.assertEqual(response.status_code, 400)
        self.assertFalse(act.called)


class TestInstructorAPIHelpers(TestCase):
    """ Test helpers for instructor.api """
    def test_split_input_list(self):
        strings = []
        lists = []
        strings.append("Lorem@ipsum.dolor, sit@amet.consectetur\nadipiscing@elit.Aenean\r convallis@at.lacus\r, ut@lacinia.Sed")
        lists.append(['Lorem@ipsum.dolor', 'sit@amet.consectetur', 'adipiscing@elit.Aenean', 'convallis@at.lacus', 'ut@lacinia.Sed'])

        for (stng, lst) in zip(strings, lists):
            self.assertEqual(_split_input_list(stng), lst)

    def test_split_input_list_unicode(self):
        self.assertEqual(_split_input_list('robot@robot.edu, robot2@robot.edu'), ['robot@robot.edu', 'robot2@robot.edu'])
        self.assertEqual(_split_input_list(u'robot@robot.edu, robot2@robot.edu'), ['robot@robot.edu', 'robot2@robot.edu'])
        self.assertEqual(_split_input_list(u'robot@robot.edu, robot2@robot.edu'), [u'robot@robot.edu', 'robot2@robot.edu'])
        scary_unistuff = unichr(40960) + u'abcd' + unichr(1972)
        self.assertEqual(_split_input_list(scary_unistuff), [scary_unistuff])

    def test_msk_from_problem_urlname(self):
        args = ('MITx/6.002x/2013_Spring', 'L2Node1')
        output = 'i4x://MITx/6.002x/problem/L2Node1'
        self.assertEqual(_msk_from_problem_urlname(*args), output)

    @raises(ValueError)
    def test_msk_from_problem_urlname_error(self):
        args = ('notagoodcourse', 'L2Node1')
        _msk_from_problem_urlname(*args)
