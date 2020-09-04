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
    """Test class for testing fetch & update of api:v1:discussion_settings endpoint."""

    discussion_settings_keys = [
        'discussion_blackouts',
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
        return reverse('api:v1:discussion_settings-detail', kwargs={
            'pk': course_key
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
        ({'allow_anonymous': False}, status.HTTP_200_OK),
        ({'allow_anonymous': True}, status.HTTP_200_OK),
        ({'discussion_blackouts': [["2015-09-15", "2015-09-21"]]}, status.HTTP_200_OK),
        ({'discussion_blackouts': [["2015-09-15T04:24", "2015-09-21T11:12"]]}, status.HTTP_200_OK),
        ({'discussion_blackouts': [["2015-09-21", "2015-09-15"]]}, status.HTTP_400_BAD_REQUEST),
        ({'discussion_blackouts': [["Invalid Date", "Should Throw Error"]]}, status.HTTP_400_BAD_REQUEST),
        ({'allow_anonymous': 2}, status.HTTP_400_BAD_REQUEST),  # invalid format
    )
    @unpack
    def test_update_discussion_settings(self, test_data, status_code):
        """Test if the endpoint updates data correctly"""
        url = self._get_discussion_settings_url()
        resp = self.client.put(url, test_data, format='json')
        assert resp.status_code == status_code

        discussion_settings = resp.json()

        # only check updated value if status code is 200
        if status_code == status.HTTP_200_OK:
            for key, val in test_data.items():
                assert discussion_settings[key] == val
        else:
            # should be a dictionary of errors
            assert isinstance(discussion_settings, dict)

    def test_persistance(self):
        url = self._get_discussion_settings_url()
        resp = self.client.get(url)
        discussion_settings = resp.json()

        # initially should be empty
        self.assertEqual(discussion_settings['discussion_blackouts'], [])

        # update with new value
        updated_value = [["2015-09-15", "2015-09-21"]]
        self.client.put(url, {'discussion_blackouts': updated_value}, format='json')

        # new get request should return new values
        resp = self.client.get(url)
        discussion_settings = resp.json()

        self.assertEqual(discussion_settings['discussion_blackouts'], updated_value)

    def test_unauthenticated_user(self):
        url = self._get_discussion_settings_url()
        client = APIClient()
        resp = client.get(url)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
