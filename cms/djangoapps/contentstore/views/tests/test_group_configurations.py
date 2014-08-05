"""
Group Configuration Tests.
"""
import json
from mock import patch
from contentstore.utils import reverse_course_url, reverse_usage_url
from contentstore.views.component import SPLIT_TEST_COMPONENT_TYPE
from contentstore.views.course import GroupConfiguration
from contentstore.tests.utils import CourseTestCase
from util.testing import UrlResetMixin
from xmodule.partitions.partitions import Group, UserPartition
from xmodule.modulestore.tests.factories import ItemFactory
from xmodule.split_test_module import ValidationMessage, ValidationMessageType

GROUP_CONFIGURATION_JSON = {
    u'name': u'Test name',
    u'description': u'Test description',
    u'groups': [
        {u'name': u'Group A'},
        {u'name': u'Group B'},
    ],
}


# pylint: disable=no-member
class HelperMethods(object):
    """
    Mixin that provides useful methods for Group Configuration tests.
    """
    def _create_content_experiment(self, cid=-1, name_suffix=''):
        """
        Create content experiment.

        Assign Group Configuration to the experiment if cid is provided.
        """
        vertical = ItemFactory.create(
            category='vertical',
            parent_location=self.course.location,
            display_name='Test Unit {}'.format(name_suffix)
        )
        c0_url = self.course.id.make_usage_key("vertical", "split_test_cond0")
        c1_url = self.course.id.make_usage_key("vertical", "split_test_cond1")
        c2_url = self.course.id.make_usage_key("vertical", "split_test_cond2")
        split_test = ItemFactory.create(
            category='split_test',
            parent_location=vertical.location,
            user_partition_id=cid,
            display_name='Test Content Experiment {}'.format(name_suffix),
            group_id_to_child={"0": c0_url, "1": c1_url, "2": c2_url}
        )
        ItemFactory.create(
            parent_location=split_test.location,
            category="vertical",
            display_name="Condition 0 vertical",
            location=c0_url,
        )
        ItemFactory.create(
            parent_location=split_test.location,
            category="vertical",
            display_name="Condition 1 vertical",
            location=c1_url,
        )
        ItemFactory.create(
            parent_location=split_test.location,
            category="vertical",
            display_name="Condition 2 vertical",
            location=c2_url,
        )

        partitions_json = [p.to_json() for p in self.course.user_partitions]

        self.client.ajax_post(
            reverse_usage_url("xblock_handler", split_test.location),
            data={'metadata': {'user_partitions': partitions_json}}
        )

        self.save_course()
        return (vertical, split_test)

    def _add_user_partitions(self, count=1):
        """
        Create user partitions for the course.
        """
        partitions = [
            UserPartition(
                i, 'Name ' + str(i), 'Description ' + str(i), [Group(0, 'Group A'), Group(1, 'Group B'), Group(2, 'Group C')]
            ) for i in xrange(0, count)
        ]

        self.course.user_partitions = partitions
        self.save_course()


# pylint: disable=no-member
class GroupConfigurationsBaseTestCase(object):
    """
    Mixin with base test cases for the group configurations.
    """
    def _remove_ids(self, content):
        """
        Remove ids from the response. We cannot predict IDs, because they're
        generated randomly.
        We use this method to clean up response when creating new group configurations.
        Returns a tuple that contains removed group configuration ID and group IDs.
        """
        configuration_id = content.pop("id")
        group_ids = [group.pop("id") for group in content["groups"]]

        return (configuration_id, group_ids)

    def test_required_fields_are_absent(self):
        """
        Test required fields are absent.
        """
        bad_jsons = [
            # must have name of the configuration
            {
                u'description': 'Test description',
                u'groups': [
                    {u'name': u'Group A'},
                    {u'name': u'Group B'},
                ],
            },
            # must have at least two groups
            {
                u'name': u'Test name',
                u'description': u'Test description',
                u'groups': [
                    {u'name': u'Group A'},
                ],
            },
            # an empty json
            {},
        ]

        for bad_json in bad_jsons:
            response = self.client.post(
                self._url(),
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
            self._url(),
            data=invalid_json,
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("Location", response)
        content = json.loads(response.content)
        self.assertIn("error", content)


# pylint: disable=no-member
class GroupConfigurationsListHandlerTestCase(UrlResetMixin, CourseTestCase, GroupConfigurationsBaseTestCase, HelperMethods):
    """
    Test cases for group_configurations_list_handler.
    """
    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_GROUP_CONFIGURATIONS": True})
    def setUp(self):
        """
        Set up GroupConfigurationsListHandlerTestCase.
        """
        super(GroupConfigurationsListHandlerTestCase, self).setUp()

    def _url(self):
        """
        Return url for the handler.
        """
        return reverse_course_url('group_configurations_list_handler', self.course.id)

    def test_view_index_ok(self):
        """
        Basic check that the groups configuration page responds correctly.
        """

        self.course.user_partitions = [
            UserPartition(0, 'First name', 'First description', [Group(0, 'Group A'), Group(1, 'Group B'), Group(2, 'Group C')]),
        ]
        self.save_course()

        if SPLIT_TEST_COMPONENT_TYPE not in self.course.advanced_modules:
            self.course.advanced_modules.append(SPLIT_TEST_COMPONENT_TYPE)
            self.store.update_item(self.course, self.user.id)

        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'First name')
        self.assertContains(response, 'Group C')

    def test_view_index_disabled(self):
        """
        Check that group configuration page is not displayed when turned off.
        """
        if SPLIT_TEST_COMPONENT_TYPE in self.course.advanced_modules:
            self.course.advanced_modules.remove(SPLIT_TEST_COMPONENT_TYPE)
            self.store.update_item(self.course, self.user.id)

        resp = self.client.get(self._url())
        self.assertContains(resp, "module is disabled")

    def test_unsupported_http_accept_header(self):
        """
        Test if not allowed header present in request.
        """
        response = self.client.get(
            self._url(),
            HTTP_ACCEPT="text/plain",
        )
        self.assertEqual(response.status_code, 406)

    def test_can_create_group_configuration(self):
        """
        Test that you can create a group configuration.
        """
        expected = {
            u'description': u'Test description',
            u'name': u'Test name',
            u'version': 1,
            u'groups': [
                {u'name': u'Group A', u'version': 1},
                {u'name': u'Group B', u'version': 1},
            ],
        }
        response = self.client.post(
            self._url(),
            data=json.dumps(GROUP_CONFIGURATION_JSON),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("Location", response)
        content = json.loads(response.content)
        configuration_id, group_ids = self._remove_ids(content)  # pylint: disable=unused-variable
        self.assertEqual(content, expected)
        # IDs are unique
        self.assertEqual(len(group_ids), len(set(group_ids)))
        self.assertEqual(len(group_ids), 2)
        self.reload_course()
        # Verify that user_partitions in the course contains the new group configuration.
        user_partititons = self.course.user_partitions
        self.assertEqual(len(user_partititons), 1)
        self.assertEqual(user_partititons[0].name, u'Test name')
        self.assertEqual(len(user_partititons[0].groups), 2)
        self.assertEqual(user_partititons[0].groups[0].name, u'Group A')
        self.assertEqual(user_partititons[0].groups[1].name, u'Group B')


# pylint: disable=no-member
class GroupConfigurationsDetailHandlerTestCase(UrlResetMixin, CourseTestCase, GroupConfigurationsBaseTestCase, HelperMethods):
    """
    Test cases for group_configurations_detail_handler.
    """

    ID = 0

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_GROUP_CONFIGURATIONS": True})
    def setUp(self):
        """
        Set up GroupConfigurationsDetailHandlerTestCase.
        """
        super(GroupConfigurationsDetailHandlerTestCase, self).setUp()

    def _url(self, cid=-1):
        """
        Return url for the handler.
        """
        cid = cid if cid > 0 else self.ID
        return reverse_course_url(
            'group_configurations_detail_handler',
            self.course.id,
            kwargs={'group_configuration_id': cid},
        )

    def test_can_create_new_group_configuration_if_it_is_not_exist(self):
        """
        PUT new group configuration when no configurations exist in the course.
        """
        expected = {
            u'id': 999,
            u'name': u'Test name',
            u'description': u'Test description',
            u'version': 1,
            u'groups': [
                {u'id': 0, u'name': u'Group A', u'version': 1},
                {u'id': 1, u'name': u'Group B', u'version': 1},
            ],
            u'usage': [],
        }

        response = self.client.put(
            self._url(cid=999),
            data=json.dumps(expected),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        content = json.loads(response.content)
        self.assertEqual(content, expected)
        self.reload_course()
        # Verify that user_partitions in the course contains the new group configuration.
        user_partititons = self.course.user_partitions
        self.assertEqual(len(user_partititons), 1)
        self.assertEqual(user_partititons[0].name, u'Test name')
        self.assertEqual(len(user_partititons[0].groups), 2)
        self.assertEqual(user_partititons[0].groups[0].name, u'Group A')
        self.assertEqual(user_partititons[0].groups[1].name, u'Group B')

    def test_can_edit_group_configuration(self):
        """
        Edit group configuration and check its id and modified fields.
        """
        self._add_user_partitions()
        self.save_course()

        expected = {
            u'id': self.ID,
            u'name': u'New Test name',
            u'description': u'New Test description',
            u'version': 1,
            u'groups': [
                {u'id': 0, u'name': u'New Group Name', u'version': 1},
                {u'id': 2, u'name': u'Group C', u'version': 1},
            ],
            u'usage': [],
        }

        response = self.client.put(
            self._url(),
            data=json.dumps(expected),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        content = json.loads(response.content)
        self.assertEqual(content, expected)
        self.reload_course()

        # Verify that user_partitions is properly updated in the course.
        user_partititons = self.course.user_partitions

        self.assertEqual(len(user_partititons), 1)
        self.assertEqual(user_partititons[0].name, u'New Test name')
        self.assertEqual(len(user_partititons[0].groups), 2)
        self.assertEqual(user_partititons[0].groups[0].name, u'New Group Name')
        self.assertEqual(user_partititons[0].groups[1].name, u'Group C')

    def test_can_delete_group_configuration(self):
        """
        Delete group configuration and check user partitions.
        """
        self._add_user_partitions(count=2)
        self.save_course()

        response = self.client.delete(
            self._url(cid=0),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 204)
        self.reload_course()
        # Verify that user_partitions is properly updated in the course.
        user_partititons = self.course.user_partitions
        self.assertEqual(len(user_partititons), 1)
        self.assertEqual(user_partititons[0].name, 'Name 1')

    def test_cannot_delete_used_group_configuration(self):
        """
        Cannot delete group configuration if it is in use.
        """
        self._add_user_partitions(count=2)
        self._create_content_experiment(cid=0)

        response = self.client.delete(
            self._url(cid=0),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        content = json.loads(response.content)
        self.assertTrue(content['error'])
        self.reload_course()
        # Verify that user_partitions is still the same.
        user_partititons = self.course.user_partitions
        self.assertEqual(len(user_partititons), 2)
        self.assertEqual(user_partititons[0].name, 'Name 0')

    def test_cannot_delete_non_existent_group_configuration(self):
        """
        Cannot delete group configuration if it is doesn't exist.
        """
        self._add_user_partitions(count=2)
        response = self.client.delete(
            self._url(cid=999),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 404)
        # Verify that user_partitions is still the same.
        user_partititons = self.course.user_partitions
        self.assertEqual(len(user_partititons), 2)
        self.assertEqual(user_partititons[0].name, 'Name 0')


# pylint: disable=no-member
class GroupConfigurationsUsageInfoTestCase(UrlResetMixin, CourseTestCase, HelperMethods):
    """
    Tests for usage information of configurations.
    """

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_GROUP_CONFIGURATIONS": True})
    def setUp(self):
        super(GroupConfigurationsUsageInfoTestCase, self).setUp()

    def test_group_configuration_not_used(self):
        """
        Test that right data structure will be created if group configuration is not used.
        """
        self._add_user_partitions()
        actual = GroupConfiguration.add_usage_info(self.course, self.store)
        expected = [{
            'id': 0,
            'name': 'Name 0',
            'description': 'Description 0',
            'version': 1,
            'groups': [
                {'id': 0, 'name': 'Group A', 'version': 1},
                {'id': 1, 'name': 'Group B', 'version': 1},
                {'id': 2, 'name': 'Group C', 'version': 1},
            ],
            'usage': [],
        }]
        self.assertEqual(actual, expected)

    def test_can_get_correct_usage_info(self):
        """
        Test if group configurations json updated successfully with usage information.
        """
        self._add_user_partitions(count=2)
        self._create_content_experiment(cid=0, name_suffix='0')
        self._create_content_experiment(name_suffix='1')

        actual = GroupConfiguration.add_usage_info(self.course, self.store)

        expected = [{
            'id': 0,
            'name': 'Name 0',
            'description': 'Description 0',
            'version': 1,
            'groups': [
                {'id': 0, 'name': 'Group A', 'version': 1},
                {'id': 1, 'name': 'Group B', 'version': 1},
                {'id': 2, 'name': 'Group C', 'version': 1},
            ],
            'usage': [{
                'url': '/container/i4x://MITx/999/vertical/Test_Unit_0',
                'label': 'Test Unit 0 / Test Content Experiment 0',
                'validation': None,
            }],
        }, {
            'id': 1,
            'name': 'Name 1',
            'description': 'Description 1',
            'version': 1,
            'groups': [
                {'id': 0, 'name': 'Group A', 'version': 1},
                {'id': 1, 'name': 'Group B', 'version': 1},
                {'id': 2, 'name': 'Group C', 'version': 1},
            ],
            'usage': [],
        }]

        self.assertEqual(actual, expected)

    def test_can_use_one_configuration_in_multiple_experiments(self):
        """
        Test if multiple experiments are present in usage info when they use same
        group configuration.
        """
        self._add_user_partitions()
        self._create_content_experiment(cid=0, name_suffix='0')
        self._create_content_experiment(cid=0, name_suffix='1')

        actual = GroupConfiguration.add_usage_info(self.course, self.store)

        expected = [{
            'id': 0,
            'name': 'Name 0',
            'description': 'Description 0',
            'version': 1,
            'groups': [
                {'id': 0, 'name': 'Group A', 'version': 1},
                {'id': 1, 'name': 'Group B', 'version': 1},
                {'id': 2, 'name': 'Group C', 'version': 1},
            ],
            'usage': [{
                'url': '/container/i4x://MITx/999/vertical/Test_Unit_0',
                'label': 'Test Unit 0 / Test Content Experiment 0',
                'validation': None,
            }, {
                'url': '/container/i4x://MITx/999/vertical/Test_Unit_1',
                'label': 'Test Unit 1 / Test Content Experiment 1',
                'validation': None,
            }],
        }]
        self.assertEqual(actual, expected)

    def test_can_handle_without_parent(self):
        """
        Test if it possible to handle case when split_test has no parent.
        """
        self._add_user_partitions()
        # Create split test without parent.
        ItemFactory.create(
            category='split_test',
            user_partition_id=0,
            display_name='Test Content Experiment'
        )
        self.save_course()
        actual = GroupConfiguration.get_usage_info(self.course, self.store)
        self.assertEqual(actual, {0: []})


class GroupConfigurationsValidationTestCase(CourseTestCase, HelperMethods):
    """
    Tests for validation in Group Configurations.
    """
    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_GROUP_CONFIGURATIONS": True})
    def setUp(self):
        super(GroupConfigurationsValidationTestCase, self).setUp()

    @patch('xmodule.split_test_module.SplitTestDescriptor.validation_messages')
    def test_error_message_present(self, mocked_validation_messages):
        """
        Tests if validation message is present.
        """
        self._add_user_partitions()
        split_test = self._create_content_experiment(cid=0, name_suffix='0')[1]

        mocked_validation_messages.return_value = [
            ValidationMessage(
                split_test,
                u"Validation message",
                ValidationMessageType.error
            )
        ]
        group_configuration = GroupConfiguration.add_usage_info(self.course, self.store)[0]
        self.assertEqual(
            group_configuration['usage'][0]['validation'],
            {
                'message': u'This content experiment has issues that affect content visibility.',
                'type': 'error'
            }
        )

    @patch('xmodule.split_test_module.SplitTestDescriptor.validation_messages')
    def test_warning_message_present(self, mocked_validation_messages):
        """
        Tests if validation message is present.
        """
        self._add_user_partitions()
        split_test = self._create_content_experiment(cid=0, name_suffix='0')[1]

        mocked_validation_messages.return_value = [
            ValidationMessage(
                split_test,
                u"Validation message",
                ValidationMessageType.warning
            )
        ]
        group_configuration = GroupConfiguration.add_usage_info(self.course, self.store)[0]
        self.assertEqual(
            group_configuration['usage'][0]['validation'],
            {
                'message': u'This content experiment has issues that affect content visibility.',
                'type': 'warning'
            }
        )

    @patch('xmodule.split_test_module.SplitTestDescriptor.validation_messages')
    def test_update_usage_info(self, mocked_validation_messages):
        """
        Tests if validation message is present when updating usage info.
        """
        self._add_user_partitions()
        split_test = self._create_content_experiment(cid=0, name_suffix='0')[1]

        mocked_validation_messages.return_value = [
            ValidationMessage(
                split_test,
                u"Validation message",
                ValidationMessageType.warning
            )
        ]

        group_configuration = GroupConfiguration.update_usage_info(self.store, self.course, self.course.user_partitions[0])

        self.assertEqual(
            group_configuration['usage'][0]['validation'],
            {
                'message': u'This content experiment has issues that affect content visibility.',
                'type': 'warning'
            }
        )

    @patch('xmodule.split_test_module.SplitTestDescriptor.validation_messages')
    def test_update_usage_info_no_message(self, mocked_validation_messages):
        """
        Tests if validation message is not present when updating usage info.
        """
        self._add_user_partitions()
        self._create_content_experiment(cid=0, name_suffix='0')
        mocked_validation_messages.return_value = []
        group_configuration = GroupConfiguration.update_usage_info(self.store, self.course, self.course.user_partitions[0])
        self.assertEqual(group_configuration['usage'][0]['validation'], None)
