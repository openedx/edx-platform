# pylint: disable=E1101, W0201
"""
Tests for Courses
"""
import httpretty
import json
from django.core.urlresolvers import reverse

from xmodule.modulestore.tests.factories import CourseFactory
from opaque_keys.edx.keys import CourseKey
from ..test_utils import SocialFacebookTestCase


class TestCourses(SocialFacebookTestCase):
    """
    Tests for /api/mobile/v0.5/courses/...
    """
    def setUp(self):
        super(TestCourses, self).setUp()
        self.course = CourseFactory.create(mobile_available=True)

    @httpretty.activate
    def test_one_course_with_friends(self):
        self.user_create_and_signin(1)
        self.link_edx_account_to_social(self.users[1], self.BACKEND, self.USERS[1]['FB_ID'])
        self.set_sharing_preferences(self.users[1], True)
        self.set_facebook_interceptor_for_friends(
            {'data': [{'name': self.USERS[1]['USERNAME'], 'id': self.USERS[1]['FB_ID']}]}
        )
        self.enroll_in_course(self.users[1], self.course)
        url = reverse('courses-with-friends')
        response = self.client.get(url, {'oauth_token': self._FB_USER_ACCESS_TOKEN})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.course.id, CourseKey.from_string(response.data[0]['course']['id']))   # pylint: disable=E1101

    @httpretty.activate
    def test_two_courses_with_friends(self):
        self.user_create_and_signin(1)
        self.link_edx_account_to_social(self.users[1], self.BACKEND, self.USERS[1]['FB_ID'])
        self.set_sharing_preferences(self.users[1], True)
        self.enroll_in_course(self.users[1], self.course)
        self.course_2 = CourseFactory.create(mobile_available=True)
        self.enroll_in_course(self.users[1], self.course_2)
        self.set_facebook_interceptor_for_friends(
            {'data': [{'name': self.USERS[2]['USERNAME'], 'id': self.USERS[1]['FB_ID']}]}
        )
        url = reverse('courses-with-friends')
        response = self.client.get(url, {'oauth_token': self._FB_USER_ACCESS_TOKEN})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.course.id, CourseKey.from_string(response.data[0]['course']['id']))  # pylint: disable=E1101
        self.assertEqual(self.course_2.id, CourseKey.from_string(response.data[1]['course']['id']))  # pylint: disable=E1101

    @httpretty.activate
    def test_three_courses_but_only_two_unique(self):
        self.user_create_and_signin(1)
        self.link_edx_account_to_social(self.users[1], self.BACKEND, self.USERS[1]['FB_ID'])
        self.set_sharing_preferences(self.users[1], True)
        self.course_2 = CourseFactory.create(mobile_available=True)
        self.enroll_in_course(self.users[1], self.course_2)
        self.enroll_in_course(self.users[1], self.course)
        self.user_create_and_signin(2)
        self.link_edx_account_to_social(self.users[2], self.BACKEND, self.USERS[2]['FB_ID'])
        self.set_sharing_preferences(self.users[2], True)
        # Enroll another user in course_2
        self.enroll_in_course(self.users[2], self.course_2)
        self.set_facebook_interceptor_for_friends(
            {'data': [
                {'name': self.USERS[1]['USERNAME'], 'id': self.USERS[1]['FB_ID']},
                {'name': self.USERS[2]['USERNAME'], 'id': self.USERS[2]['FB_ID']},
            ]}
        )
        url = reverse('courses-with-friends')
        response = self.client.get(url, {'oauth_token': self._FB_USER_ACCESS_TOKEN})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.course.id, CourseKey.from_string(response.data[0]['course']['id']))  # pylint: disable=E1101
        self.assertEqual(self.course_2.id, CourseKey.from_string(response.data[1]['course']['id']))  # pylint: disable=E1101
        # Assert that only two courses are returned
        self.assertEqual(len(response.data), 2)  # pylint: disable=E1101

    @httpretty.activate
    def test_two_courses_with_two_friends_on_different_paged_results(self):
        self.user_create_and_signin(1)
        self.link_edx_account_to_social(self.users[1], self.BACKEND, self.USERS[1]['FB_ID'])
        self.set_sharing_preferences(self.users[1], True)
        self.enroll_in_course(self.users[1], self.course)

        self.user_create_and_signin(2)
        self.link_edx_account_to_social(self.users[2], self.BACKEND, self.USERS[2]['FB_ID'])
        self.set_sharing_preferences(self.users[2], True)
        self.course_2 = CourseFactory.create(mobile_available=True)
        self.enroll_in_course(self.users[2], self.course_2)
        self.set_facebook_interceptor_for_friends(
            {
                'data': [{'name': self.USERS[1]['USERNAME'], 'id': self.USERS[1]['FB_ID']}],
                "paging": {"next": "https://graph.facebook.com/v2.2/me/friends/next"},
                "summary": {"total_count": 652}
            }
        )
        # Set the interceptor for the paged
        httpretty.register_uri(
            httpretty.GET,
            "https://graph.facebook.com/v2.2/me/friends/next",
            body=json.dumps(
                {
                    "data": [{'name': self.USERS[2]['USERNAME'], 'id': self.USERS[2]['FB_ID']}],
                    "paging": {
                        "previous":
                        "https://graph.facebook.com/v2.2/10154805434030300/friends?limit=25&offset=25"
                    },
                    "summary": {"total_count": 652}
                }
            ),
            status=201
        )

        url = reverse('courses-with-friends')
        response = self.client.get(url, {'oauth_token': self._FB_USER_ACCESS_TOKEN})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.course.id, CourseKey.from_string(response.data[0]['course']['id']))  # pylint: disable=E1101
        self.assertEqual(self.course_2.id, CourseKey.from_string(response.data[1]['course']['id']))  # pylint: disable=E1101

    @httpretty.activate
    def test_no_courses_with_friends_because_sharing_pref_off(self):
        self.user_create_and_signin(1)
        self.link_edx_account_to_social(self.users[1], self.BACKEND, self.USERS[1]['FB_ID'])
        self.set_sharing_preferences(self.users[1], False)
        self.set_facebook_interceptor_for_friends(
            {'data': [{'name': self.USERS[1]['USERNAME'], 'id': self.USERS[1]['FB_ID']}]}
        )
        self.enroll_in_course(self.users[1], self.course)
        url = reverse('courses-with-friends')
        response = self.client.get(url, {'oauth_token': self._FB_USER_ACCESS_TOKEN})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    @httpretty.activate
    def test_no_courses_with_friends_because_no_auth_token(self):
        self.user_create_and_signin(1)
        self.link_edx_account_to_social(self.users[1], self.BACKEND, self.USERS[1]['FB_ID'])
        self.set_sharing_preferences(self.users[1], False)
        self.set_facebook_interceptor_for_friends(
            {'data': [{'name': self.USERS[1]['USERNAME'], 'id': self.USERS[1]['FB_ID']}]}
        )
        self.enroll_in_course(self.users[1], self.course)
        url = reverse('courses-with-friends')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
