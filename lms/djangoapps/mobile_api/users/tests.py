"""
Tests for users API
"""
from rest_framework.test import APITestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from courseware.tests.factories import StaffFactory, UserFactory
from django.core.urlresolvers import reverse
from mobile_api.users.serializers import CourseEnrollmentSerializer
from student.models import CourseEnrollment


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

    def enroll(self):
        resp = self.client.post(reverse('change_enrollment'), {
            'enrollment_action': 'enroll',
            'course_id': self.course.id.to_deprecated_string(),
            'check_access': True,
        })
        self.assertEqual(resp.status_code, 200)

    def test_user_enrollments(self):
        url = reverse('courseenrollment-detail', kwargs={'username': self.user.username})

        self.client.login(username=self.username, password=self.password)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

        self.enroll()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        courses = response.data

        self.assertTrue(len(courses), 1)
        course = courses[0]['course']
        self.assertTrue('video_outline' in course)
        self.assertTrue('course_handouts' in course)
        self.assertEqual(course['id'], self.course.id.to_deprecated_string())
        self.assertEqual(courses[0]['mode'], 'honor')

    def test_user_overview(self):
        self.client.login(username=self.username, password=self.password)
        url = reverse('user-detail', kwargs={'username': self.user.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.data
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
        self.enroll()
        serialized = CourseEnrollmentSerializer(CourseEnrollment.enrollments_for_user(self.user)[0]).data
        self.assertEqual(serialized['course']['video_outline'], None)
        self.assertEqual(serialized['course']['name'], self.course.display_name)
