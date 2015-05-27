# pylint: disable=E1101
"""
Tests for friends
"""
import json
import httpretty
from django.core.urlresolvers import reverse
from xmodule.modulestore.tests.factories import CourseFactory
from ..test_utils import SocialFacebookTestCase


class TestFriends(SocialFacebookTestCase):
    """
    Tests for /api/mobile/v0.5/friends/...
    """

    def setUp(self):
        super(TestFriends, self).setUp()
        self.course = CourseFactory.create()

    @httpretty.activate
    def test_no_friends_enrolled(self):
        # User 1 set up
        self.user_create_and_signin(1)
        # Link user_1's edX account to FB
        self.link_edx_account_to_social(self.users[1], self.BACKEND, self.USERS[1]['FB_ID'])
        self.set_sharing_preferences(self.users[1], True)
        # Set the interceptor
        self.set_facebook_interceptor_for_friends(
            {
                'data':
                    [
                        {'name': self.USERS[1]['USERNAME'], 'id': self.USERS[1]['FB_ID']},
                        {'name': self.USERS[2]['USERNAME'], 'id': self.USERS[2]['FB_ID']},
                        {'name': self.USERS[3]['USERNAME'], 'id': self.USERS[3]['FB_ID']},
                    ]
            }
        )
        course_id = unicode(self.course.id)
        url = reverse('friends-in-course', kwargs={"course_id": course_id})
        response = self.client.get(url, {'format': 'json', 'oauth_token': self._FB_USER_ACCESS_TOKEN})
        # Assert that no friends are returned
        self.assertEqual(response.status_code, 200)
        self.assertTrue('friends' in response.data and len(response.data['friends']) == 0)

    @httpretty.activate
    def test_no_friends_on_facebook(self):
        # User 1 set up
        self.user_create_and_signin(1)
        # Enroll user_1 in the course
        self.enroll_in_course(self.users[1], self.course)
        self.set_sharing_preferences(self.users[1], True)
        # Link user_1's edX account to FB
        self.link_edx_account_to_social(self.users[1], self.BACKEND, self.USERS[1]['FB_ID'])
        # Set the interceptor
        self.set_facebook_interceptor_for_friends({'data': []})
        course_id = unicode(self.course.id)
        url = reverse('friends-in-course', kwargs={"course_id": course_id})
        response = self.client.get(
            url, {'format': 'json', 'oauth_token': self._FB_USER_ACCESS_TOKEN}
        )
        # Assert that no friends are returned
        self.assertEqual(response.status_code, 200)
        self.assertTrue('friends' in response.data and len(response.data['friends']) == 0)

    @httpretty.activate
    def test_no_friends_linked_to_edx(self):
        # User 1 set up
        self.user_create_and_signin(1)
        # Enroll user_1 in the course
        self.enroll_in_course(self.users[1], self.course)
        self.set_sharing_preferences(self.users[1], True)
        # User 2 set up
        self.user_create_and_signin(2)
        # Enroll user_2 in the course
        self.enroll_in_course(self.users[2], self.course)
        self.set_sharing_preferences(self.users[2], True)
        # User 3 set up
        self.user_create_and_signin(3)
        # Enroll user_3 in the course
        self.enroll_in_course(self.users[3], self.course)
        self.set_sharing_preferences(self.users[3], True)

        # Set the interceptor
        self.set_facebook_interceptor_for_friends(
            {
                'data':
                    [
                        {'name': self.USERS[1]['USERNAME'], 'id': self.USERS[1]['FB_ID']},
                        {'name': self.USERS[2]['USERNAME'], 'id': self.USERS[2]['FB_ID']},
                        {'name': self.USERS[3]['USERNAME'], 'id': self.USERS[3]['FB_ID']},
                    ]
            }
        )
        course_id = unicode(self.course.id)
        url = reverse('friends-in-course', kwargs={"course_id": course_id})
        response = self.client.get(
            url,
            {'format': 'json', 'oauth_token': self._FB_USER_ACCESS_TOKEN}
        )
        # Assert that no friends are returned
        self.assertEqual(response.status_code, 200)
        self.assertTrue('friends' in response.data and len(response.data['friends']) == 0)

    @httpretty.activate
    def test_no_friends_share_settings_false(self):
        # User 1 set up
        self.user_create_and_signin(1)
        self.enroll_in_course(self.users[1], self.course)
        self.link_edx_account_to_social(self.users[1], self.BACKEND, self.USERS[1]['FB_ID'])
        self.set_sharing_preferences(self.users[1], False)
        self.set_facebook_interceptor_for_friends(
            {
                'data':
                    [
                        {'name': self.USERS[1]['USERNAME'], 'id': self.USERS[1]['FB_ID']},
                        {'name': self.USERS[2]['USERNAME'], 'id': self.USERS[2]['FB_ID']},
                        {'name': self.USERS[3]['USERNAME'], 'id': self.USERS[3]['FB_ID']},
                    ]
            }
        )
        url = reverse('friends-in-course', kwargs={"course_id": unicode(self.course.id)})
        response = self.client.get(url, {'format': 'json', 'oauth_token': self._FB_USER_ACCESS_TOKEN})

        # Assert that USERNAME_1 is returned
        self.assertEqual(response.status_code, 200)
        self.assertTrue('friends' in response.data)
        self.assertTrue('friends' in response.data and len(response.data['friends']) == 0)

    @httpretty.activate
    def test_no_friends_no_oauth_token(self):
        # User 1 set up
        self.user_create_and_signin(1)
        self.enroll_in_course(self.users[1], self.course)
        self.link_edx_account_to_social(self.users[1], self.BACKEND, self.USERS[1]['FB_ID'])
        self.set_sharing_preferences(self.users[1], False)
        self.set_facebook_interceptor_for_friends(
            {
                'data':
                    [
                        {'name': self.USERS[1]['USERNAME'], 'id': self.USERS[1]['FB_ID']},
                        {'name': self.USERS[2]['USERNAME'], 'id': self.USERS[2]['FB_ID']},
                        {'name': self.USERS[3]['USERNAME'], 'id': self.USERS[3]['FB_ID']},
                    ]
            }
        )
        url = reverse('friends-in-course', kwargs={"course_id": unicode(self.course.id)})
        response = self.client.get(url, {'format': 'json'})
        # Assert that USERNAME_1 is returned
        self.assertEqual(response.status_code, 400)

    @httpretty.activate
    def test_one_friend_in_course(self):
        # User 1 set up
        self.user_create_and_signin(1)
        self.enroll_in_course(self.users[1], self.course)
        self.link_edx_account_to_social(self.users[1], self.BACKEND, self.USERS[1]['FB_ID'])
        self.set_sharing_preferences(self.users[1], True)
        self.set_facebook_interceptor_for_friends(
            {
                'data':
                    [
                        {'name': self.USERS[1]['USERNAME'], 'id': self.USERS[1]['FB_ID']},
                        {'name': self.USERS[2]['USERNAME'], 'id': self.USERS[2]['FB_ID']},
                        {'name': self.USERS[3]['USERNAME'], 'id': self.USERS[3]['FB_ID']},
                    ]
            }
        )
        url = reverse('friends-in-course', kwargs={"course_id": unicode(self.course.id)})
        response = self.client.get(url, {'format': 'json', 'oauth_token': self._FB_USER_ACCESS_TOKEN})

        # Assert that USERNAME_1 is returned
        self.assertEqual(response.status_code, 200)
        self.assertTrue('friends' in response.data)
        self.assertTrue('id' in response.data['friends'][0])
        self.assertTrue(response.data['friends'][0]['id'] == self.USERS[1]['FB_ID'])
        self.assertTrue('name' in response.data['friends'][0])
        self.assertTrue(response.data['friends'][0]['name'] == self.USERS[1]['USERNAME'])

    @httpretty.activate
    def test_three_friends_in_course(self):
        # User 1 set up
        self.user_create_and_signin(1)
        self.enroll_in_course(self.users[1], self.course)
        self.link_edx_account_to_social(self.users[1], self.BACKEND, self.USERS[1]['FB_ID'])
        self.set_sharing_preferences(self.users[1], True)

        # User 2 set up
        self.user_create_and_signin(2)
        self.enroll_in_course(self.users[2], self.course)
        self.link_edx_account_to_social(self.users[2], self.BACKEND, self.USERS[2]['FB_ID'])
        self.set_sharing_preferences(self.users[2], True)

        # User 3 set up
        self.user_create_and_signin(3)
        self.enroll_in_course(self.users[3], self.course)
        self.link_edx_account_to_social(self.users[3], self.BACKEND, self.USERS[3]['FB_ID'])
        self.set_sharing_preferences(self.users[3], True)
        self.set_facebook_interceptor_for_friends(
            {
                'data':
                    [
                        {'name': self.USERS[1]['USERNAME'], 'id': self.USERS[1]['FB_ID']},
                        {'name': self.USERS[2]['USERNAME'], 'id': self.USERS[2]['FB_ID']},
                        {'name': self.USERS[3]['USERNAME'], 'id': self.USERS[3]['FB_ID']},
                    ]
            }
        )
        url = reverse('friends-in-course', kwargs={"course_id": unicode(self.course.id)})
        response = self.client.get(
            url,
            {'format': 'json', 'oauth_token': self._FB_USER_ACCESS_TOKEN}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue('friends' in response.data)
        # Assert that USERNAME_1 is returned
        self.assertTrue(
            'id' in response.data['friends'][0] and
            response.data['friends'][0]['id'] == self.USERS[1]['FB_ID']
        )
        self.assertTrue(
            'name' in response.data['friends'][0] and
            response.data['friends'][0]['name'] == self.USERS[1]['USERNAME']
        )
        # Assert that USERNAME_2 is returned
        self.assertTrue(
            'id' in response.data['friends'][1] and
            response.data['friends'][1]['id'] == self.USERS[2]['FB_ID']
        )
        self.assertTrue(
            'name' in response.data['friends'][1] and
            response.data['friends'][1]['name'] == self.USERS[2]['USERNAME']
        )
        # Assert that USERNAME_3 is returned
        self.assertTrue(
            'id' in response.data['friends'][2] and
            response.data['friends'][2]['id'] == self.USERS[3]['FB_ID']
        )
        self.assertTrue(
            'name' in response.data['friends'][2] and
            response.data['friends'][2]['name'] == self.USERS[3]['USERNAME']
        )

    @httpretty.activate
    def test_three_friends_in_paged_response(self):
        # User 1 set up
        self.user_create_and_signin(1)
        self.enroll_in_course(self.users[1], self.course)
        self.link_edx_account_to_social(self.users[1], self.BACKEND, self.USERS[1]['FB_ID'])
        self.set_sharing_preferences(self.users[1], True)

        # User 2 set up
        self.user_create_and_signin(2)
        self.enroll_in_course(self.users[2], self.course)
        self.link_edx_account_to_social(self.users[2], self.BACKEND, self.USERS[2]['FB_ID'])
        self.set_sharing_preferences(self.users[2], True)

        # User 3 set up
        self.user_create_and_signin(3)
        self.enroll_in_course(self.users[3], self.course)
        self.link_edx_account_to_social(self.users[3], self.BACKEND, self.USERS[3]['FB_ID'])
        self.set_sharing_preferences(self.users[3], True)

        self.set_facebook_interceptor_for_friends(
            {
                'data': [{'name': self.USERS[1]['USERNAME'], 'id': self.USERS[1]['FB_ID']}],
                "paging": {"next": "https://graph.facebook.com/v2.2/me/friends/next_1"},
                "summary": {"total_count": 652}
            }
        )
        # Set the interceptor for the first paged content
        httpretty.register_uri(
            httpretty.GET,
            "https://graph.facebook.com/v2.2/me/friends/next_1",
            body=json.dumps(
                {
                    "data": [{'name': self.USERS[2]['USERNAME'], 'id': self.USERS[2]['FB_ID']}],
                    "paging": {"next": "https://graph.facebook.com/v2.2/me/friends/next_2"},
                    "summary": {"total_count": 652}
                }
            ),
            status=201
        )
        # Set the interceptor for the last paged content
        httpretty.register_uri(
            httpretty.GET,
            "https://graph.facebook.com/v2.2/me/friends/next_2",
            body=json.dumps(
                {
                    "data": [{'name': self.USERS[3]['USERNAME'], 'id': self.USERS[3]['FB_ID']}],
                    "paging": {
                        "previous":
                        "https://graph.facebook.com/v2.2/10154805434030300/friends?limit=25&offset=25"
                    },
                    "summary": {"total_count": 652}
                }
            ),
            status=201
        )
        url = reverse('friends-in-course', kwargs={"course_id": unicode(self.course.id)})
        response = self.client.get(url, {'format': 'json', 'oauth_token': self._FB_USER_ACCESS_TOKEN})
        self.assertEqual(response.status_code, 200)
        self.assertTrue('friends' in response.data)
        # Assert that USERNAME_1 is returned
        self.assertTrue('id' in response.data['friends'][0])
        self.assertTrue(response.data['friends'][0]['id'] == self.USERS[1]['FB_ID'])
        self.assertTrue('name' in response.data['friends'][0])
        self.assertTrue(response.data['friends'][0]['name'] == self.USERS[1]['USERNAME'])
        # Assert that USERNAME_2 is returned
        self.assertTrue('id' in response.data['friends'][1])
        self.assertTrue(response.data['friends'][1]['id'] == self.USERS[2]['FB_ID'])
        self.assertTrue('name' in response.data['friends'][1])
        self.assertTrue(response.data['friends'][1]['name'] == self.USERS[2]['USERNAME'])
        # Assert that USERNAME_3 is returned
        self.assertTrue('id' in response.data['friends'][2])
        self.assertTrue(response.data['friends'][2]['id'] == self.USERS[3]['FB_ID'])
        self.assertTrue('name' in response.data['friends'][2])
        self.assertTrue(response.data['friends'][2]['name'] == self.USERS[3]['USERNAME'])
