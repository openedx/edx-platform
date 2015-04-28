"""
Class for manipulating groups configuration on a course object.
"""
import json
import logging

from util.db import generate_int_id, MYSQL_MAX_INT

from django.utils.translation import ugettext as _
from contentstore.utils import reverse_usage_url
from xmodule.partitions.partitions import UserPartition
from xmodule.split_test_module import get_split_user_partitions
from openedx.core.djangoapps.course_groups.partition_scheme import get_cohorted_user_partition

MINIMUM_GROUP_ID = 100

RANDOM_SCHEME = "random"
COHORT_SCHEME = "cohort"

# Note: the following content group configuration strings are not
# translated since they are not visible to users.
CONTENT_GROUP_CONFIGURATION_DESCRIPTION = 'The groups in this configuration can be mapped to cohort groups in the LMS.'

CONTENT_GROUP_CONFIGURATION_NAME = 'Content Group Configuration'

log = logging.getLogger(__name__)


class GroupConfigurationsValidationError(Exception):
    """
    An error thrown when a group configurations input is invalid.
    """
    pass


class GroupConfiguration(object):
    """
    Prepare Group Configuration for the course.
    """
    def __init__(self, json_string, course, configuration_id=None):
        """
        Receive group configuration as a json (`json_string`), deserialize it
        and validate.
        """
        self.configuration = GroupConfiguration.parse(json_string)
        self.course = course
        self.assign_id(configuration_id)
        self.assign_group_ids()
        self.validate()

    @staticmethod
    def parse(json_string):
        """
        Deserialize given json that represents group configuration.
        """
        try:
            configuration = json.loads(json_string)
        except ValueError:
            raise GroupConfigurationsValidationError(_("invalid JSON"))
        configuration["version"] = UserPartition.VERSION
        return configuration

    def validate(self):
        """
        Validate group configuration representation.
        """
        if not self.configuration.get("name"):
            raise GroupConfigurationsValidationError(_("must have name of the configuration"))
        if len(self.configuration.get('groups', [])) < 1:
            raise GroupConfigurationsValidationError(_("must have at least one group"))

    def assign_id(self, configuration_id=None):
        """
        Assign id for the json representation of group configuration.
        """
        if configuration_id:
            self.configuration['id'] = int(configuration_id)
        else:
            self.configuration['id'] = generate_int_id(
                MINIMUM_GROUP_ID, MYSQL_MAX_INT, GroupConfiguration.get_used_ids(self.course)
            )

    def assign_group_ids(self):
        """
        Assign ids for the group_configuration's groups.
        """
        used_ids = [g.id for p in self.course.user_partitions for g in p.groups]
        # Assign ids to every group in configuration.
        for group in self.configuration.get('groups', []):
            if group.get('id') is None:
                group["id"] = generate_int_id(MINIMUM_GROUP_ID, MYSQL_MAX_INT, used_ids)
                used_ids.append(group["id"])

    @staticmethod
    def get_used_ids(course):
        """
        Return a list of IDs that already in use.
        """
        return set([p.id for p in course.user_partitions])

    def get_user_partition(self):
        """
        Get user partition for saving in course.
        """
        return UserPartition.from_json(self.configuration)

    @staticmethod
    def _get_usage_info(course, unit, item, usage_info, group_id, scheme_name=None):
        """
        Get usage info for unit/module.
        """
        unit_url = reverse_usage_url(
            'container_handler',
            course.location.course_key.make_usage_key(unit.location.block_type, unit.location.name)
        )

        usage_dict = {'label': u"{} / {}".format(unit.display_name, item.display_name), 'url': unit_url}
        if scheme_name == RANDOM_SCHEME:
            validation_summary = item.general_validation_message()
            usage_dict.update({'validation': validation_summary.to_json() if validation_summary else None})

        usage_info[group_id].append(usage_dict)

        return usage_info

    @staticmethod
    def get_content_experiment_usage_info(store, course):
        """
        Get usage information for all Group Configurations currently referenced by a split_test instance.
        """
        split_tests = store.get_items(course.id, qualifiers={'category': 'split_test'})
        return GroupConfiguration._get_content_experiment_usage_info(store, course, split_tests)

    @staticmethod
    def get_split_test_partitions_with_usage(store, course):
        """
        Returns json split_test group configurations updated with usage information.
        """
        usage_info = GroupConfiguration.get_content_experiment_usage_info(store, course)
        configurations = []
        for partition in get_split_user_partitions(course.user_partitions):
            configuration = partition.to_json()
            configuration['usage'] = usage_info.get(partition.id, [])
            configurations.append(configuration)
        return configurations

    @staticmethod
    def _get_content_experiment_usage_info(store, course, split_tests):  # pylint: disable=unused-argument
        """
        Returns all units names, their urls and validation messages.

        Returns:
        {'user_partition_id':
            [
                {
                    'label': 'Unit 1 / Experiment 1',
                    'url': 'url_to_unit_1',
                    'validation': {'message': 'a validation message', 'type': 'warning'}
                },
                {
                    'label': 'Unit 2 / Experiment 2',
                    'url': 'url_to_unit_2',
                    'validation': {'message': 'another validation message', 'type': 'error'}
                }
            ],
        }
        """
        usage_info = {}
        for split_test in split_tests:
            if split_test.user_partition_id not in usage_info:
                usage_info[split_test.user_partition_id] = []

            unit = split_test.get_parent()
            if not unit:
                log.warning("Unable to find parent for split_test %s", split_test.location)
                continue

            usage_info = GroupConfiguration._get_usage_info(
                course=course,
                unit=unit,
                item=split_test,
                usage_info=usage_info,
                group_id=split_test.user_partition_id,
                scheme_name=RANDOM_SCHEME
            )
        return usage_info

    @staticmethod
    def get_content_groups_usage_info(store, course):
        """
        Get usage information for content groups.
        """
        items = store.get_items(course.id, settings={'group_access': {'$exists': True}})

        return GroupConfiguration._get_content_groups_usage_info(course, items)

    @staticmethod
    def _get_content_groups_usage_info(course, items):
        """
        Returns all units names and their urls.

        Returns:
        {'group_id':
            [
                {
                    'label': 'Unit 1 / Problem 1',
                    'url': 'url_to_unit_1'
                },
                {
                    'label': 'Unit 2 / Problem 2',
                    'url': 'url_to_unit_2'
                }
            ],
        }
        """
        usage_info = {}
        for item in items:
            if hasattr(item, 'group_access') and item.group_access:
                (__, group_ids), = item.group_access.items()
                for group_id in group_ids:
                    if group_id not in usage_info:
                        usage_info[group_id] = []

                    unit = item.get_parent()
                    if not unit:
                        log.warning("Unable to find parent for component %s", item.location)
                        continue

                    usage_info = GroupConfiguration._get_usage_info(
                        course,
                        unit=unit,
                        item=item,
                        usage_info=usage_info,
                        group_id=group_id
                    )

        return usage_info

    @staticmethod
    def get_content_groups_items_usage_info(store, course):
        """
        Get usage information on items for content groups.
        """
        items = store.get_items(course.id, settings={'group_access': {'$exists': True}})

        return GroupConfiguration._get_content_groups_items_usage_info(course, items)

    @staticmethod
    def _get_content_groups_items_usage_info(course, items):
        """
        Returns all items names and their urls.

        Returns:
        {'group_id':
            [
                {
                    'label': 'Problem 1 / Problem 1',
                    'url': 'url_to_item_1'
                },
                {
                    'label': 'Problem 2 / Problem 2',
                    'url': 'url_to_item_2'
                }
            ],
        }
        """
        usage_info = {}
        for item in items:
            if hasattr(item, 'group_access') and item.group_access:
                (__, group_ids), = item.group_access.items()
                for group_id in group_ids:
                    if group_id not in usage_info:
                        usage_info[group_id] = []

                    usage_info = GroupConfiguration._get_usage_info(
                        course,
                        unit=item,
                        item=item,
                        usage_info=usage_info,
                        group_id=group_id
                    )

        return usage_info

    @staticmethod
    def update_usage_info(store, course, configuration):
        """
        Update usage information for particular Group Configuration.

        Returns json of particular group configuration updated with usage information.
        """
        configuration_json = None
        # Get all Experiments that use particular  Group Configuration in course.
        if configuration.scheme.name == RANDOM_SCHEME:
            split_tests = store.get_items(
                course.id,
                category='split_test',
                content={'user_partition_id': configuration.id}
            )
            configuration_json = configuration.to_json()
            usage_information = GroupConfiguration._get_content_experiment_usage_info(store, course, split_tests)
            configuration_json['usage'] = usage_information.get(configuration.id, [])
        elif configuration.scheme.name == COHORT_SCHEME:
            # In case if scheme is "cohort"
            configuration_json = GroupConfiguration.update_content_group_usage_info(store, course, configuration)
        return configuration_json

    @staticmethod
    def update_content_group_usage_info(store, course, configuration):
        """
        Update usage information for particular Content Group Configuration.

        Returns json of particular content group configuration updated with usage information.
        """
        usage_info = GroupConfiguration.get_content_groups_usage_info(store, course)
        content_group_configuration = configuration.to_json()

        for group in content_group_configuration['groups']:
            group['usage'] = usage_info.get(group['id'], [])

        return content_group_configuration

    @staticmethod
    def get_or_create_content_group(store, course):
        """
        Returns the first user partition from the course which uses the
        CohortPartitionScheme, or generates one if no such partition is
        found.  The created partition is not saved to the course until
        the client explicitly creates a group within the partition and
        POSTs back.
        """
        content_group_configuration = get_cohorted_user_partition(course.id)
        if content_group_configuration is None:
            content_group_configuration = UserPartition(
                id=generate_int_id(MINIMUM_GROUP_ID, MYSQL_MAX_INT, GroupConfiguration.get_used_ids(course)),
                name=CONTENT_GROUP_CONFIGURATION_NAME,
                description=CONTENT_GROUP_CONFIGURATION_DESCRIPTION,
                groups=[],
                scheme_id=COHORT_SCHEME
            )
            return content_group_configuration.to_json()

        content_group_configuration = GroupConfiguration.update_content_group_usage_info(
            store,
            course,
            content_group_configuration
        )
        return content_group_configuration
