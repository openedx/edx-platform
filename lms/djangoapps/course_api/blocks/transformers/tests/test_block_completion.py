"""
Tests for BlockCompletionTransformer.
"""


from completion.models import BlockCompletion
from completion.test_utils import CompletionWaffleTestMixin
from xblock.completable import CompletableXBlockMixin, XBlockCompletionMode
from xblock.core import XBlock

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.course_api.blocks.transformers.block_completion import BlockCompletionTransformer
from lms.djangoapps.course_blocks.api import get_course_blocks
from lms.djangoapps.course_blocks.transformers.tests.helpers import ModuleStoreTestCase, TransformerRegistryTestMixin
from lms.djangoapps.course_blocks.usage_info import CourseUsageInfo
from openedx.core.djangoapps.content.block_structure.factory import BlockStructureFactory
from openedx.core.djangoapps.content.block_structure.transformers import BlockStructureTransformers
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.factories import CourseFactory, BlockFactory  # lint-amnesty, pylint: disable=wrong-import-order


class StubAggregatorXBlock(XBlock):
    """
    XBlock to test behaviour of BlockCompletionTransformer
    when transforming aggregator XBlock.
    """
    completion_mode = XBlockCompletionMode.AGGREGATOR
    has_children = True


class StubExcludedXBlock(XBlock):
    """
    XBlock to test behaviour of BlockCompletionTransformer
    when transforming excluded XBlock.
    """
    completion_mode = XBlockCompletionMode.EXCLUDED


class StubCompletableXBlock(XBlock, CompletableXBlockMixin):
    """
    XBlock to test behaviour of BlockCompletionTransformer
    when transforming completable XBlock.
    """


class BlockCompletionTransformerTestCase(TransformerRegistryTestMixin, CompletionWaffleTestMixin, ModuleStoreTestCase):
    """
    Tests behaviour of BlockCompletionTransformer
    """
    TRANSFORMER_CLASS_TO_TEST = BlockCompletionTransformer
    # Has to be 1.0 for 'complete' to function properly. The Completion api only uses 0.0 and 1.0 right now
    # so this better reflects reality anyway. Should be updated if Completion api ever supports more.
    COMPLETION_TEST_VALUE = 1.0

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create(password='test')
        # Set ENABLE_COMPLETION_TRACKING waffle switch to True
        self.override_waffle_switch(True)

    @XBlock.register_temp_plugin(StubAggregatorXBlock, identifier='aggregator')
    @XBlock.register_temp_plugin(StubCompletableXBlock, identifier='comp')
    def test_transform_aggregators(self):
        """
        If there is an aggregator (such as a unit) that contains no children for some reason
        (likely a mistake by the course team), it should be marked 'complete'. 'completion' should
        still be None.
        We mark 'complete' so learners are still able to have their subsections/sections/course
        marked as complete and are not blocked by this one empty aggregator.
        """
        course = CourseFactory.create()
        # Have to have at least one complete block to trigger entering the marking 'complete' flow
        filled_aggregator = BlockFactory.create(category='aggregator', parent=course)
        block = BlockFactory.create(category='comp', parent=filled_aggregator)
        BlockCompletion.objects.submit_completion(
            user=self.user,
            block_key=block.location,
            completion=self.COMPLETION_TEST_VALUE,
        )
        empty_aggregator = BlockFactory.create(category='aggregator', parent=course)
        block_structure = get_course_blocks(self.user, course.location, self.transformers)

        self._assert_block_has_proper_completion_values(
            block_structure, block.location, self.COMPLETION_TEST_VALUE, True
        )
        self._assert_block_has_proper_completion_values(
            block_structure, filled_aggregator.location, None, True
        )
        self._assert_block_has_proper_completion_values(
            block_structure, empty_aggregator.location, None, True
        )

    @XBlock.register_temp_plugin(StubExcludedXBlock, identifier='excluded')
    def test_transform_gives_none_for_excluded(self):
        """
        Excluded blocks always receive None for 'completion' and False for 'complete'
        """
        course = CourseFactory.create()
        block = BlockFactory.create(category='excluded', parent=course)
        block_structure = get_course_blocks(self.user, course.location, self.transformers)

        self._assert_block_has_proper_completion_values(block_structure, block.location, None, False)

    @XBlock.register_temp_plugin(StubCompletableXBlock, identifier='comp')
    def test_transform_gives_value_for_completable(self):
        """
        If a block is actually complete, make sure that value shows up in the transformed fields.
        'completion' should have the value and 'complete' should be True in these cases.
        """
        course = CourseFactory.create()
        block = BlockFactory.create(category='comp', parent=course)
        BlockCompletion.objects.submit_completion(
            user=self.user,
            block_key=block.location,
            completion=self.COMPLETION_TEST_VALUE,
        )
        block_structure = get_course_blocks(self.user, course.location, self.transformers)

        self._assert_block_has_proper_completion_values(
            block_structure, block.location, self.COMPLETION_TEST_VALUE, True
        )

    def test_transform_gives_zero_for_ordinary_block(self):
        """
        I _think_ this is testing 'completion' is 0.0 before an ordinary block is viewed.
        'html' blocks end up receiving a 'completion' of 1.0 after being viewed.
        """
        course = CourseFactory.create()
        block = BlockFactory.create(category='html', parent=course)
        block_structure = get_course_blocks(self.user, course.location, self.transformers)

        self._assert_block_has_proper_completion_values(block_structure, block.location, 0.0, False)

    @XBlock.register_temp_plugin(StubAggregatorXBlock, identifier='aggregator')
    @XBlock.register_temp_plugin(StubCompletableXBlock, identifier='comp')
    def test_transform_with_unpublished_blocks_in_structure(self):
        """
        Test that when unpublished blocks are present in the block structure
        (as might happen when CMS adds them to cache), the transformer correctly
        excludes them from completion calculations by checking published_on field.

        This is a test-only scenario to verify the fix works correctly.
        """
        from xmodule.modulestore.django import modulestore

        course = CourseFactory.create()
        aggregator = BlockFactory.create(category='aggregator', parent=course)
        published_block = BlockFactory.create(category='comp', parent=aggregator)
        BlockCompletion.objects.submit_completion(
            user=self.user,
            block_key=published_block.location,
            completion=self.COMPLETION_TEST_VALUE,
        )

        # Create an unpublished block
        unpublished_block = BlockFactory.create(category='comp', parent=aggregator, publish_item=False)
        # Simulate a completion submission for the unpublished block (Should be ignored)
        BlockCompletion.objects.submit_completion(
            user=self.user,
            block_key=unpublished_block.location,
            completion=0.0,
        )

        # Now create a block structure that includes both published and unpublished blocks
        # This simulates what happens when CMS modifies the cache
        store = modulestore()
        with store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, course.id):
            # Get the course with all blocks (published and unpublished)
            draft_course = store.get_course(course.id, depth=None)
            # Create block structure from the draft course (includes unpublished)
            block_structure = BlockStructureFactory.create_from_modulestore(
                root_block_usage_key=draft_course.location,
                modulestore=store
            )
            usage_info = CourseUsageInfo(
                user=self.user,
                course_key=course.id,
            )
            transformers = BlockStructureTransformers([self.TRANSFORMER_CLASS_TO_TEST()], usage_info)
            transformers.collect(block_structure)
            transformers.transform(block_structure)

        self._assert_block_has_proper_completion_values(
            block_structure, published_block.location, self.COMPLETION_TEST_VALUE, True
        )
        self._assert_block_has_proper_completion_values(
            block_structure, unpublished_block.location, 0.0, False
        )
        self._assert_block_has_proper_completion_values(
            block_structure, aggregator.location, None, True
        )

    def _assert_block_has_proper_completion_values(
            self, block_structure, block_key, expected_completion, expected_complete
    ):
        """
        Checks whether block's completion and complete have expected values.
        """
        block_data = block_structure.get_transformer_block_data(block_key, self.TRANSFORMER_CLASS_TO_TEST)
        completion_value = block_data.fields['completion']
        # complete isn't saved as a transformer field, but just a regular xblock field /shrug
        complete_value = block_structure.get_xblock_field(block_key, 'complete', False)

        assert completion_value == expected_completion
        assert complete_value == expected_complete
