"""
Tests for manager.py
"""

import ddt
import pytest
from django.test import TestCase
from edx_toggles.toggles.testutils import override_waffle_switch

from common.djangoapps.student.tests.factories import CourseEnrollmentFactory
from lms.djangoapps.course_blocks.transformers.tests.helpers import CourseStructureTestCase
from lms.djangoapps.course_blocks.transformers.tests.test_user_partitions import UserPartitionTestMixin
from openedx.core.djangoapps.content.block_structure.api import get_block_structure_manager
from openedx.core.djangoapps.course_groups.cohorts import add_user_to_cohort

from ..block_structure import BlockStructureBlockData
from ..config import STORAGE_BACKING_FOR_CACHE
from ..exceptions import UsageKeyNotInBlockStructure
from ..manager import BlockStructureManager
from ..transformers import BlockStructureTransformers
from .helpers import (
    ChildrenMapTestMixin,
    MockCache,
    MockModulestoreFactory,
    MockTransformer,
    UsageKeyFactoryMixin,
    mock_registered_transformers
)


class TestTransformer1(MockTransformer):
    """
    Test Transformer class with basic functionality to verify collected and
    transformed data.
    """
    collect_data_key = 't1.collect'
    transform_data_key = 't1.transform'
    collect_call_count = 0

    @classmethod
    def collect(cls, block_structure):
        """
        Collects block data for the block structure.
        """
        cls._set_block_values(block_structure, cls.collect_data_key)
        cls.collect_call_count += 1

    def transform(self, usage_info, block_structure):
        """
        Transforms the block structure.
        """
        self._set_block_values(block_structure, self.transform_data_key)

    @classmethod
    def assert_collected(cls, block_structure):
        """
        Asserts data was collected for the block structure.
        """
        cls._assert_block_values(block_structure, cls.collect_data_key)

    @classmethod
    def assert_transformed(cls, block_structure):
        """
        Asserts the block structure was transformed.
        """
        cls._assert_block_values(block_structure, cls.transform_data_key)

    @classmethod
    def _set_block_values(cls, block_structure, data_key):
        """
        Sets a value for each block in the given structure, using the given
        data key.
        """
        for block_key in block_structure.topological_traversal():
            block_structure.set_transformer_block_field(
                block_key, cls, data_key, cls._create_block_value(block_key, data_key)
            )

    @classmethod
    def _assert_block_values(cls, block_structure, data_key):
        """
        Verifies the value for each block in the given structure, for the given
        data key.
        """
        for block_key in block_structure.topological_traversal():
            assert (
                block_structure.get_transformer_block_field(
                    block_key,
                    cls,
                    data_key,
                ) == cls._create_block_value(block_key, data_key)
            )

    @classmethod
    def _create_block_value(cls, block_key, data_key):
        """
        Returns a unique deterministic value for the given block key
        and data key.
        """
        return data_key + 't1.val1.' + str(block_key)


@ddt.ddt
class TestBlockStructureManager(UsageKeyFactoryMixin, ChildrenMapTestMixin, TestCase):
    """
    Test class for BlockStructureManager.
    """

    def setUp(self):
        super().setUp()

        TestTransformer1.collect_call_count = 0
        self.registered_transformers = [TestTransformer1()]
        with mock_registered_transformers(self.registered_transformers):
            self.transformers = BlockStructureTransformers(self.registered_transformers)

        self.children_map = self.SIMPLE_CHILDREN_MAP
        self.modulestore = MockModulestoreFactory.create(self.children_map, self.block_key_factory)
        self.cache = MockCache()
        self.bs_manager = BlockStructureManager(self.block_key_factory(0), self.modulestore, self.cache)

    def collect_and_verify(self, expect_modulestore_called, expect_cache_updated):
        """
        Calls the manager's get_collected method and verifies its result
        and behavior.
        """
        self.modulestore.get_items_call_count = 0
        self.cache.set_call_count = 0
        with mock_registered_transformers(self.registered_transformers):
            block_structure = self.bs_manager.get_collected()
        self.assert_block_structure(block_structure, self.children_map)
        TestTransformer1.assert_collected(block_structure)
        if expect_modulestore_called:
            assert self.modulestore.get_items_call_count > 0
        else:
            assert self.modulestore.get_items_call_count == 0
        expected_count = 1 if expect_cache_updated else 0
        assert self.cache.set_call_count == expected_count

    def test_get_transformed(self):
        with mock_registered_transformers(self.registered_transformers):
            block_structure = self.bs_manager.get_transformed(self.transformers)
        self.assert_block_structure(block_structure, self.children_map)
        TestTransformer1.assert_collected(block_structure)
        TestTransformer1.assert_transformed(block_structure)

    def test_get_transformed_with_starting_block(self):
        with mock_registered_transformers(self.registered_transformers):
            block_structure = self.bs_manager.get_transformed(
                self.transformers,
                starting_block_usage_key=self.block_key_factory(1),
            )
        substructure_of_children_map = [[], [3, 4], [], [], []]
        self.assert_block_structure(block_structure, substructure_of_children_map, missing_blocks=[0, 2])
        TestTransformer1.assert_collected(block_structure)
        TestTransformer1.assert_transformed(block_structure)

    def test_get_transformed_with_collected(self):
        with mock_registered_transformers(self.registered_transformers):
            collected_block_structure = self.bs_manager.get_collected()

        # using the same collected block structure,
        # transform at different starting blocks
        for (starting_block, expected_structure, expected_missing_blocks) in [
                (0, [[1, 2], [3, 4], [], [], []], []),
                (1, [[], [3, 4], [], [], []], [0, 2]),
                (2, [[], [], [], [], []], [0, 1, 3, 4]),
        ]:
            block_structure = self.bs_manager.get_transformed(
                self.transformers,
                starting_block_usage_key=self.block_key_factory(starting_block),
                collected_block_structure=collected_block_structure,
            )
            self.assert_block_structure(block_structure, expected_structure, missing_blocks=expected_missing_blocks)

    def test_get_transformed_with_nonexistent_starting_block(self):
        with mock_registered_transformers(self.registered_transformers):
            with pytest.raises(UsageKeyNotInBlockStructure):
                self.bs_manager.get_transformed(self.transformers, starting_block_usage_key=100)

    def test_get_collected_cached(self):
        self.collect_and_verify(expect_modulestore_called=True, expect_cache_updated=True)
        self.collect_and_verify(expect_modulestore_called=False, expect_cache_updated=False)
        assert TestTransformer1.collect_call_count == 1

    @ddt.data(True, False)
    def test_update_collected_if_needed(self, with_storage_backing):
        with override_waffle_switch(STORAGE_BACKING_FOR_CACHE, active=with_storage_backing):
            with mock_registered_transformers(self.registered_transformers):
                assert TestTransformer1.collect_call_count == 0

                self.bs_manager.update_collected_if_needed()
                assert TestTransformer1.collect_call_count == 1

                self.bs_manager.update_collected_if_needed()
                expected_count = 1 if with_storage_backing else 2
                assert TestTransformer1.collect_call_count == expected_count

                self.collect_and_verify(expect_modulestore_called=False, expect_cache_updated=False)

    def test_get_collected_transformer_version(self):
        self.collect_and_verify(expect_modulestore_called=True, expect_cache_updated=True)

        # transformer code writes new schema version; data not re-collected
        TestTransformer1.WRITE_VERSION += 1
        self.collect_and_verify(expect_modulestore_called=False, expect_cache_updated=False)

        # transformer code requires new schema version; data re-collected
        TestTransformer1.READ_VERSION += 1
        self.collect_and_verify(expect_modulestore_called=True, expect_cache_updated=True)

        # old transformer code can read new schema version; data not re-collected
        TestTransformer1.READ_VERSION -= 1
        self.collect_and_verify(expect_modulestore_called=False, expect_cache_updated=False)

        assert TestTransformer1.collect_call_count == 2

    def test_get_collected_structure_version(self):
        self.collect_and_verify(expect_modulestore_called=True, expect_cache_updated=True)
        BlockStructureBlockData.VERSION += 1
        self.collect_and_verify(expect_modulestore_called=True, expect_cache_updated=True)
        assert TestTransformer1.collect_call_count == 2

    def test_clear(self):
        self.collect_and_verify(expect_modulestore_called=True, expect_cache_updated=True)
        self.bs_manager.clear()
        self.collect_and_verify(expect_modulestore_called=True, expect_cache_updated=True)
        assert TestTransformer1.collect_call_count == 2


@ddt.ddt
class TestBlockStructureManagerGetCollected(UserPartitionTestMixin, CourseStructureTestCase):
    """
    Tests `BlockStructureManager.get_collected`
    """

    def setup_partitions_and_course(self):
        """
        Setup course structure and create user.
        """
        # Set up user partitions and groups.
        self.setup_groups_partitions(active=True)
        self.user_partition = self.user_partitions[0]

        # Build course.
        self.course_hierarchy = self.get_course_hierarchy()
        self.blocks = self.build_course(self.course_hierarchy)
        self.course = self.blocks['course']

        # Enroll user in course.
        CourseEnrollmentFactory.create(
            user=self.user, course_id=self.course.id, is_active=True
        )

        # Set up cohorts.
        self.setup_cohorts(self.course)

    def get_course_hierarchy(self):
        """
        Returns a course hierarchy to test with.
        """
        #                                     course
        #                                  /          \
        #                                 /            \
        #                      A[1, 2, 3]                B
        #                     /  |      \                |
        #                   /    |       \               |
        #                 /      |        \              |
        #           C[1, 2]    D[2, 3]     E            /
        #         / |     \      |        / \          /
        #        /  |     \      |       /   \        /
        #       /   |     \      |      /     \      /
        #     F   G[1]   H[2]    I     J     K[4]   /
        #        /   \    /                  /  \  /
        #       /    \   /                  /   \ /
        #      /     \  /                  /    \/
        #  L[1, 2]  M[1, 2, 3]            N     O
        #
        return [
            {
                'org': 'UserPartitionTransformer',
                'course': 'UP101F',
                'run': 'test_run',
                'user_partitions': [self.user_partition],
                '#type': 'course',
                '#ref': 'course',
                '#children': [
                    {
                        '#type': 'vertical',
                        '#ref': 'A',
                        'metadata': {'group_access': {self.user_partition.id: [0, 1, 2, 3]}},
                    },
                    {'#type': 'vertical', '#ref': 'B'},
                ],
            },
            {
                '#type': 'vertical',
                '#ref': 'C',
                '#parents': ['A'],
                'metadata': {'group_access': {self.user_partition.id: [1, 2]}},
                '#children': [
                    {'#type': 'vertical', '#ref': 'F'},
                    {
                        '#type': 'vertical',
                        '#ref': 'G',
                        'metadata': {'group_access': {self.user_partition.id: [1]}},
                    },
                    {
                        '#type': 'vertical',
                        '#ref': 'H',
                        'metadata': {'group_access': {self.user_partition.id: [2]}},
                    },
                ],
            },
            {
                '#type': 'vertical',
                '#ref': 'D',
                '#parents': ['A'],
                'metadata': {'group_access': {self.user_partition.id: [2, 3]}},
                '#children': [{'#type': 'vertical', '#ref': 'I'}],
            },
            {
                '#type': 'vertical',
                '#ref': 'E',
                '#parents': ['A'],
                '#children': [{'#type': 'vertical', '#ref': 'J'}],
            },
            {
                '#type': 'vertical',
                '#ref': 'K',
                '#parents': ['E'],
                'metadata': {'group_access': {self.user_partition.id: [4, 51]}},
                '#children': [{'#type': 'vertical', '#ref': 'N'}],
            },
            {
                '#type': 'vertical',
                '#ref': 'L',
                '#parents': ['G'],
                'metadata': {'group_access': {self.user_partition.id: [1, 2]}},
            },
            {
                '#type': 'vertical',
                '#ref': 'M',
                '#parents': ['G', 'H'],
                'metadata': {'group_access': {self.user_partition.id: [1, 2, 3]}},
            },
            {
                '#type': 'vertical',
                '#ref': 'O',
                '#parents': ['K', 'B'],
            },
        ]

    @ddt.data(
        (None, ('course', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O')),
        (1, ('course', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O')),
        (2, ('course', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O')),
        (3, ('course', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O')),
        (4, ('course', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O')),
    )
    @ddt.unpack
    def test_get_collected(self, group_id, expected_blocks):
        """
        Test that `BlockStructureManager.get_collected` returns all course blocks regardless of the user group.
        """
        self.setup_partitions_and_course()
        if group_id:
            cohort = self.partition_cohorts[self.user_partition.id - 1][group_id - 1]
            add_user_to_cohort(cohort, self.user.username)

        trans_block_structure = get_block_structure_manager(self.course.location.course_key).get_collected(self.user)
        self.assertSetEqual(
            set(trans_block_structure.get_block_keys()),
            self.get_block_key_set(self.blocks, *expected_blocks)
        )
