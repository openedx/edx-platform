"""Tests for discussion settings endpoint"""


from ddt import data, ddt, unpack
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from student.tests.factories import TEST_PASSWORD, AdminFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@ddt
class DiscussionSettingsTests(ModuleStoreTestCase):

    discussion_settings_keys = [
        'discussion_blackouts',
        'discussion_link',
        'discussion_sort_alpha',
        'allow_anonymous_to_peers',
        'allow_anonymous'
    ]

    def setUp(self):
        super(DiscussionSettingsTests, self).setUp()
        self.client = APIClient()
        user = AdminFactory()
        self.client.login(username=user.username, password=TEST_PASSWORD)
        self.course = CourseFactory.create(org='edX', number='test_course_key', display_name='Test Course')

    def _get_discussion_settings_url(self):
        course_key = 'edX/test_course_key/Test_Course'
        return reverse('api:v1:discussion_settings', kwargs={
            'course_key_string': course_key
        })

    def test_fetch_discussion_settings(self):
        """Test if the endpoint returns data correctly"""
        url = self._get_discussion_settings_url()
        resp = self.client.get(url)

        assert resp.status_code == status.HTTP_200_OK

        discussion_settings = resp.json()
        for key in self.discussion_settings_keys:
            assert key in discussion_settings

    @data(
        ({'allow_anonymous': {'value': False}}, status.HTTP_200_OK),
        ({'allow_anonymous': {'value': False}}, status.HTTP_200_OK),
        ({'allow_anonymous': 2}, status.HTTP_400_BAD_REQUEST),  # invalid format
    )
    @unpack
    def test_update_discussion_settings(self, data, status_code):
        """Test if the endpoint updates data correctly"""
        url = self._get_discussion_settings_url()
        resp = self.client.post(url, data, format='json')
        assert resp.status_code == status_code

        discussion_settings = resp.json()

        # only check updated value if status code is 200
        if status_code == status.HTTP_200_OK:
            for key, val in data.items():
                assert discussion_settings[key]['value'] == val['value']
        else:
            assert "errors" in discussion_settings

    def test_unauthenticated_user(self):
        url = self._get_discussion_settings_url()
        client = APIClient()
        resp = client.get(url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN
