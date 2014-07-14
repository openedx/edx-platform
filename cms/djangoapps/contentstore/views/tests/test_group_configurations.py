import json
from unittest import skipUnless
from django.conf import settings
from contentstore.utils import reverse_course_url
from contentstore.tests.utils import CourseTestCase


@skipUnless(settings.FEATURES.get('ENABLE_GROUP_CONFIGURATIONS'), 'Tests Group Configurations feature')
class GroupConfigurationsCreateTestCase(CourseTestCase):
    """
    Test cases for creating a new group configurations.
    """

    def setUp(self):
        """
        Set up a url and group configuration content for tests.
        """
        super(GroupConfigurationsCreateTestCase, self).setUp()
        self.url = reverse_course_url('group_configurations_list_handler', self.course.id)
        self.group_configuration_json = {
            u'description': u'Test description',
            u'name': u'Test name'
        }

    def test_index_page(self):
        """
        Check that the group configuration index page responds correctly.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('New Group Configuration', response.content)

    def test_group_success(self):
        """
        Test that you can create a group configuration.
        """
        expected_group_configuration = {
            u'description': u'Test description',
            u'name': u'Test name',
            u'version': 1,
            u'groups': [
                {u'id': 0, u'name': u'Group A', u'version': 1},
                {u'id': 1, u'name': u'Group B', u'version': 1}
            ]
        }
        response = self.client.post(
            self.url,
            data=json.dumps(self.group_configuration_json),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("Location", response)
        group_configuration = json.loads(response.content)
        del group_configuration['id']  # do not check for id, it is unique
        self.assertEqual(expected_group_configuration, group_configuration)

    def test_bad_group(self):
        """
        Test if only one group in configuration exist.
        """
        # Only one group in group configuration here.
        bad_group_configuration = {
            u'description': u'Test description',
            u'id': 1,
            u'name': u'Test name',
            u'version': 1,
            u'groups': [
                {u'id': 0, u'name': u'Group A', u'version': 1},
            ]
        }
        response = self.client.post(
            self.url,
            data=json.dumps(bad_group_configuration),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("Location", response)
        content = json.loads(response.content)
        self.assertIn("error", content)

    def test_bad_configuration_id(self):
        """
        Test if configuration id is not numeric.
        """
        # Configuration id is string here.
        bad_group_configuration = {
            u'description': u'Test description',
            u'id': 'bad_id',
            u'name': u'Test name',
            u'version': 1,
            u'groups': [
                {u'id': 0, u'name': u'Group A', u'version': 1},
                {u'id': 1, u'name': u'Group B', u'version': 1}
            ]
        }
        response = self.client.post(
            self.url,
            data=json.dumps(bad_group_configuration),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("Location", response)
        content = json.loads(response.content)
        self.assertIn("error", content)

    def test_bad_json(self):
        """
        Test bad json handling.
        """
        bad_jsons = [
            {u'name': 'Test Name'},
            {u'description': 'Test description'},
            {}
        ]
        for bad_json in bad_jsons:
            response = self.client.post(
                self.url,
                data=json.dumps(bad_json),
                content_type="application/json",
                HTTP_ACCEPT="application/json",
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
            self.assertEqual(response.status_code, 400)
            self.assertNotIn("Location", response)
            content = json.loads(response.content)
            self.assertIn("error", content)

    def test_invalid_json(self):
        """
        Test invalid json handling.
        """
        # No property name.
        invalid_json = "{u'name': 'Test Name', []}"

        response = self.client.post(
            self.url,
            data=invalid_json,
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("Location", response)
        content = json.loads(response.content)
        self.assertIn("error", content)
