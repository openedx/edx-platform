"""
Tests for users API
"""

import ddt
from rest_framework.test import APITestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from courseware.tests.factories import UserFactory
from django.core.urlresolvers import reverse
from mobile_api.users.serializers import CourseEnrollmentSerializer
from student.models import CourseEnrollment
from student import auth


@ddt.ddt
class TestUserApi(ModuleStoreTestCase, APITestCase):
    """
    Test the user info API
    """
    def setUp(self):
        super(TestUserApi, self).setUp()
        self.course = CourseFactory.create(mobile_available=True)
        self.user = UserFactory.create()
        self.password = 'test'
        self.username = self.user.username

    def tearDown(self):
        super(TestUserApi, self).tearDown()
        self.client.logout()

    def _enrollment_url(self):
        """
        api url that gets the current user's course enrollments
        """
        return reverse('courseenrollment-detail', kwargs={'username': self.user.username})

    def _enroll(self, course):
        """
        enroll test user in test course
        """
        resp = self.client.post(reverse('change_enrollment'), {
            'enrollment_action': 'enroll',
            'course_id': course.id.to_deprecated_string(),
            'check_access': True,
        })
        self.assertEqual(resp.status_code, 200)

    def _verify_single_course_enrollment(self, course):
        """
        check that enrolling in course adds us to it
        """

        url = self._enrollment_url()
        self.client.login(username=self.username, password=self.password)
        self._enroll(course)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        courses = response.data   # pylint: disable=maybe-no-member
        self.assertEqual(len(courses), 1)

        found_course = courses[0]['course']
        self.assertTrue('video_outline' in found_course)
        self.assertTrue('course_handouts' in found_course)
        self.assertEqual(found_course['id'], unicode(course.id))
        self.assertEqual(courses[0]['mode'], 'honor')

    def test_non_mobile_enrollments(self):
        url = self._enrollment_url()
        non_mobile_course = CourseFactory.create(mobile_available=False)
        self.client.login(username=self.username, password=self.password)

        self._enroll(non_mobile_course)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])    # pylint: disable=maybe-no-member

    @ddt.data(auth.CourseBetaTesterRole, auth.CourseStaffRole, auth.CourseInstructorRole)
    def test_privileged_enrollments(self, role):
        non_mobile_course = CourseFactory.create(mobile_available=False)
        role(non_mobile_course.id).add_users(self.user)

        self._verify_single_course_enrollment(non_mobile_course)

    def test_mobile_enrollments(self):
        self._verify_single_course_enrollment(self.course)

    def test_user_overview(self):
        self.client.login(username=self.username, password=self.password)
        url = reverse('user-detail', kwargs={'username': self.user.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.data  # pylint: disable=maybe-no-member
        self.assertEqual(data['username'], self.user.username)
        self.assertEqual(data['email'], self.user.email)

    def test_overview_anon(self):
        # anonymous disallowed
        url = reverse('user-detail', kwargs={'username': self.user.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        # can't get info on someone else
        other = UserFactory.create()
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('user-detail', kwargs={'username': other.username}))
        self.assertEqual(response.status_code, 403)

    def test_redirect_userinfo(self):
        url = '/api/mobile/v0.5/my_user_info'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        self.client.login(username=self.username, password=self.password)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.username in response['location'])

    def test_course_serializer(self):
        self.client.login(username=self.username, password=self.password)
        self._enroll(self.course)
        serialized = CourseEnrollmentSerializer(CourseEnrollment.enrollments_for_user(self.user)[0]).data  # pylint: disable=E1101
        self.assertEqual(serialized['course']['video_outline'], None)
        self.assertEqual(serialized['course']['name'], self.course.display_name)
