"""
    Test utils for Facebook functionality
"""

import httpretty
import json

from rest_framework.test import APITestCase
from django.conf import settings
from django.core.urlresolvers import reverse
from social.apps.django_app.default.models import UserSocialAuth

from student.models import CourseEnrollment
from student.views import login_oauth_token
from openedx.core.djangoapps.user_api.preferences.api import get_user_preference, set_user_preference

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from courseware.tests.factories import UserFactory


class SocialFacebookTestCase(ModuleStoreTestCase, APITestCase):
    """
    Base Class for social test cases
    """

    USERS = {
        1: {'USERNAME': "TestUser One",
            'EMAIL': "test_one@ebnotions.com",
            'PASSWORD': "edx",
            'FB_ID': "11111111111111111"},
        2: {'USERNAME': "TestUser Two",
            'EMAIL': "test_two@ebnotions.com",
            'PASSWORD': "edx",
            'FB_ID': "22222222222222222"},
        3: {'USERNAME': "TestUser Three",
            'EMAIL': "test_three@ebnotions.com",
            'PASSWORD': "edx",
            'FB_ID': "33333333333333333"}
    }

    BACKEND = "facebook"
    USER_URL = "https://graph.facebook.com/me"
    UID_FIELD = "id"

    _FB_USER_ACCESS_TOKEN = 'ThisIsAFakeFacebookToken'

    users = {}

    def setUp(self):
        super(SocialFacebookTestCase, self).setUp()

    def set_facebook_interceptor_for_access_token(self):
        """
        Facebook interceptor for groups access_token
        """
        httpretty.register_uri(
            httpretty.GET,
            'https://graph.facebook.com/oauth/access_token?client_secret=' +
            settings.FACEBOOK_APP_SECRET + '&grant_type=client_credentials&client_id=' +
            settings.FACEBOOK_APP_ID,
            body='FakeToken=FakeToken',
            status=200
        )

    def set_facebook_interceptor_for_groups(self, data, status):
        """
        Facebook interceptor for groups test
        """
        httpretty.register_uri(
            httpretty.POST,
            'https://graph.facebook.com/' + settings.FACEBOOK_API_VERSION +
            '/' + settings.FACEBOOK_APP_ID + '/groups',
            body=json.dumps(data),
            status=status
        )

    def set_facebook_interceptor_for_members(self, data, status, group_id, member_id):
        """
        Facebook interceptor for group members tests
        """
        httpretty.register_uri(
            httpretty.POST,
            'https://graph.facebook.com/' + settings.FACEBOOK_API_VERSION +
            '/' + group_id + '/members?member=' + member_id +
            '&access_token=FakeToken',
            body=json.dumps(data),
            status=status
        )

    def set_facebook_interceptor_for_friends(self, data):
        """
       Facebook interceptor for friends tests
        """
        httpretty.register_uri(
            httpretty.GET,
            "https://graph.facebook.com/v2.2/me/friends",
            body=json.dumps(data),
            status=201
        )

    def delete_group(self, group_id):
        """
        Invoke the delete groups view
        """
        url = reverse('create-delete-group', kwargs={'group_id': group_id})
        response = self.client.delete(url)
        return response

    def invite_to_group(self, group_id, member_ids):
        """
        Invoke the invite to group view
        """
        url = reverse('add-remove-member', kwargs={'group_id': group_id, 'member_id': ''})
        return self.client.post(url, {'member_ids': member_ids})

    def remove_from_group(self, group_id, member_id):
        """
        Invoke the remove from group view
        """
        url = reverse('add-remove-member', kwargs={'group_id': group_id, 'member_id': member_id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)

    def link_edx_account_to_social(self, user, backend, social_uid):
        """
        Register the user to the social auth backend
        """
        reverse(login_oauth_token, kwargs={"backend": backend})
        UserSocialAuth.objects.create(user=user, provider=backend, uid=social_uid)

    def set_sharing_preferences(self, user, boolean_value):
        """
        Sets self.user's share settings to boolean_value
        """
        # Note that setting the value to boolean will result in the conversion to the unicode form of the boolean.
        set_user_preference(user, 'share_with_facebook_friends', boolean_value)
        self.assertEqual(get_user_preference(user, 'share_with_facebook_friends'), unicode(boolean_value))

    def _change_enrollment(self, action, course_id=None, email_opt_in=None):
        """
        Change the student's enrollment status in a course.

        Args:
            action (string): The action to perform (either "enroll" or "unenroll")

        Keyword Args:
            course_id (unicode): If provided, use this course ID.  Otherwise, use the
                course ID created in the setup for this test.
            email_opt_in (unicode): If provided, pass this value along as
                an additional GET parameter.
        """
        if course_id is None:
            course_id = unicode(self.course.id)

        params = {
            'enrollment_action': action,
            'course_id': course_id
        }

        if email_opt_in:
            params['email_opt_in'] = email_opt_in

        return self.client.post(reverse('change_enrollment'), params)

    def user_create_and_signin(self, user_number):
        """
        Create a user and sign them in
        """
        self.users[user_number] = UserFactory.create(
            username=self.USERS[user_number]['USERNAME'],
            email=self.USERS[user_number]['EMAIL'],
            password=self.USERS[user_number]['PASSWORD']
        )
        self.client.login(username=self.USERS[user_number]['USERNAME'], password=self.USERS[user_number]['PASSWORD'])

    def enroll_in_course(self, user, course):
        """
        Enroll a user in the course
        """
        resp = self._change_enrollment('enroll', course_id=course.id)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(CourseEnrollment.is_enrolled(user, course.id))
        course_mode, is_active = CourseEnrollment.enrollment_mode_for_user(user, course.id)
        self.assertTrue(is_active)
        self.assertEqual(course_mode, 'honor')
