"""
Unit tests for instructor.api methods.
"""

import json
from urllib import quote
from django.test import TestCase
from nose.tools import raises
from django.test.utils import override_settings
from django.core.urlresolvers import reverse

from courseware.tests.modulestore_config import TEST_DATA_MONGO_MODULESTORE
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from courseware.tests.helpers import LoginEnrollmentTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory, AdminFactory

from student.models import CourseEnrollment

from instructor.views.api import _split_input_list, _msk_from_problem_urlname


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestInstructorAPIDenyLevels(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Ensure that users cannot access endpoints they shouldn't be able to.
    """
    def setUp(self):
        self.user = UserFactory.create()
        self.course = CourseFactory.create()
        CourseEnrollment.objects.create(user=self.user, course_id=self.course.id)
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

# class TestInstructorAPILevelsEnrollment
# # students_update_enrollment

# class TestInstructorAPILevelsAccess
# # modify_access
# # list_course_role_members


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestInstructorAPILevelsDataDump(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test endpoints that show data without side effects.
    """
    def setUp(self):
        self.instructor = AdminFactory.create()
        self.course = CourseFactory.create()
        self.client.login(username=self.instructor.username, password='test')

        # self.students = [UserFactory(email="foobar{}@robot.org".format(i)) for i in xrange(6)]
        self.students = [UserFactory() for _ in xrange(6)]
        for student in self.students:
            CourseEnrollment.objects.create(user=student, course_id=self.course.id)

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
        url += "?student_email={}".format(
            quote(self.students[0].email.encode("utf-8"))
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

# class TestInstructorAPILevelsGrade modification & tasks
# # reset_student_attempts
# # rescore_problem
# # list_instructor_tasks

# class TestInstructorAPILevelsForums
# # list_forum_members
# # update_forum_role_membership


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
