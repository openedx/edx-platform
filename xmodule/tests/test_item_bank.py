"""
Unit tests for ItemBankBlock.

@TODO - work in progress
"""

from unittest.mock import MagicMock, Mock, patch

import ddt
from bson.objectid import ObjectId
from fs.memoryfs import MemoryFS
from lxml import etree
from opaque_keys.edx.locator import LibraryLocator
from rest_framework import status
from search.search_engine_base import SearchEngine
from web_fragments.fragment import Fragment
from xblock.runtime import Runtime as VanillaRuntime

from openedx.core.djangolib.testing.utils import skip_unless_cms
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.utils import MixedSplitTestCase
from xmodule.tests import prepare_block_runtime
from xmodule.validation import StudioValidationMessage
from xmodule.x_module import AUTHOR_VIEW
from xmodule.capa_block import ProblemBlock
from common.djangoapps.student.tests.factories import UserFactory

from ..item_bank_block import ItemBankBlock
from .test_course_block import DummySystem as TestImportSystem

dummy_render = lambda block, _: Fragment(block.data)  # pylint: disable=invalid-name


class ItemBankTestMixin(MixedSplitTestCase):
    """
    Base class for tests of ItemBankBlock
    """

    def setUp(self):
        super().setUp()
        self.user_id = UserFactory().id
        self.course = CourseFactory.create(modulestore=self.store)
        self.chapter = self.make_block(category="chapter", parent_block=self.course)
        self.sequential = self.make_block(category="sequential", parent_block=self.chapter)
        self.vertical = self.make_block(category="vertical", parent_block=self.sequential)
        self.item_bank = self.make_block(
            category="itembank", parent_block=self.vertical, max_count=1, display_name="My Item Bank"
        )
        self.items = [
            self.make_block(category="problem", parent_block=self.item_bank, display_name=f"Item {i}")
            for i in range(4)
        ]
        self.item_bank = self.store.get_item(self.item_bank.usage_key, self.user_id)

    def _bind_course_block(self, block):
        """
        Bind a block (part of self.course) so we can access student-specific data.

        @@TODO is this necessary?
        """
        prepare_block_runtime(block.runtime, course_id=block.location.course_key)

        def get_block(descriptor):
            """Mocks module_system get_block function"""
            prepare_block_runtime(descriptor.runtime, course_id=block.location.course_key)
            descriptor.runtime.get_block_for_descriptor = get_block
            descriptor.bind_for_student(self.user_id)
            return descriptor

        block.runtime.get_block_for_descriptor = get_block


@skip_unless_cms
class TestItemBankExportImport(ItemBankTestMixin):
    """
    Export and import tests for ItemBankBlock
    """
    def setUp(self):
        super().setUp()
        self.expected_olx = (
            '<itembank display_name="My Item Bank" max_count="1">\n'
            '  <problem url_name="Item_0"/>\n'
            '  <problem url_name="Item_1"/>\n'
            '  <problem url_name="Item_2"/>\n'
            '  <problem url_name="Item_3"/>\n'
            '</itembank>\n'
        )

        # Set the virtual FS to export the olx to.
        self.export_fs = MemoryFS()
        self.item_bank.runtime.export_fs = self.export_fs  # pylint: disable=protected-access

        # Prepare runtime for the import.
        self.runtime = TestImportSystem(load_error_blocks=True, course_id=self.item_bank.location.course_key)
        self.runtime.resources_fs = self.export_fs
        self.id_generator = Mock()

        # Export the olx.
        node = etree.Element("unknown_root")
        self.item_bank.add_xml_to_node(node)

    def _verify_xblock_properties(self, imported_item_bank):
        """
        Check the new XBlock has the same properties as the old one.
        """
        assert imported_item_bank.display_name == self.item_bank.display_name
        assert imported_item_bank.max_count == self.item_bank.max_count
        assert len(imported_item_bank.children) == len(self.item_bank.children)

    def test_xml_export_import_cycle(self):
        """
        Test the export-import cycle.
        """
        # Read back the olx.
        with self.export_fs.open('{dir}/{file_name}.xml'.format(
            dir=self.item_bank.scope_ids.usage_id.block_type,
            file_name=self.item_bank.scope_ids.usage_id.block_id
        )) as f:
            exported_olx = f.read()

        # And compare.
        assert exported_olx == self.expected_olx

        # Now import it.
        olx_element = etree.fromstring(exported_olx)
        imported_item_bank = ItemBankBlock.parse_xml(olx_element, self.runtime, None)

        self._verify_xblock_properties(imported_item_bank)

    def test_xml_import_with_comments(self):
        """
        Test that XML comments within ItemBankBlock are ignored during the import.
        """
        olx_with_comments = (
            '<!-- Comment -->\n'
            '<itembank display_name="My Item Bank" max_count="1">\n'
            '<!-- Comment -->\n'
            '  <problem url_name="Item_0"/>\n'
            '  <problem url_name="Item_1"/>\n'
            '  <problem url_name="Item_2"/>\n'
            '  <problem url_name="Item_3"/>\n'
            '</itembank>\n'
        )

        # Import the olx.
        olx_element = etree.fromstring(olx_with_comments)
        imported_item_bank = ItemBankBlock.parse_xml(olx_element, self.runtime, None)

        self._verify_xblock_properties(imported_item_bank)


@ddt.ddt
class ItemBankTestsMore(ItemBankTestMixin):
    """
    @@TODO
    """
    def setUp(self):
        super().setUp()

    def test_children_seen_by_a_user(self):
        """
        Test that each student sees only one block as a child of the LibraryContent block.
        """
        self._bind_course_block(self.item_bank)
        # Make sure the runtime knows that the block's children vary per-user:
        assert self.item_bank.has_dynamic_children()

        assert len(self.item_bank.children) == len(self.items)

        # Check how many children each user will see:
        assert len(self.item_bank.get_child_blocks()) == 1
        # Check that get_content_titles() doesn't return titles for hidden/unused children
        assert len(self.item_bank.get_content_titles()) == 1


    def _assert_has_only_N_matching_problems(self, result, n):
        assert result.summary
        assert StudioValidationMessage.WARNING == result.summary.type
        assert f'only {n} matching problem' in result.summary.text

    def test_validation_of_matching_blocks(self):
        """
        Test that the validation method of LibraryContent blocks can warn
        the user about problems with other settings (max_count and capa_type).

        @@TODO
        """
        # Ensure we're starting wtih clean validation
        assert self.item_bank.validate()

        return  # @@TODO finish implementing this test case

        # Set max_count to higher value than exists in library
        self.item_bank.max_count = 50
        result = self.item_bank.validate()
        assert not result
        self._assert_has_only_N_matching_problems(result, 4)
        assert len(self.item_bank.selected_children()) == 4

        # Add some capa problems so we can check problem type validation messages
        self.item_bank.max_count = 1
        assert self.item_bank.validate()
        assert len(self.item_bank.selected_children()) == 1

        # Existing problem type should pass validation
        self.item_bank.capa_type = 'multiplechoiceresponse'
        self._sync_lc_block_from_library()
        self.item_bank.max_count = 1
        assert self.item_bank.validate()
        assert len(self.item_bank.selected_children()) == 1

        # ... unless requested more blocks than exists in library
        self.item_bank.capa_type = 'multiplechoiceresponse'
        self._sync_lc_block_from_library()
        self.item_bank.max_count = 10
        result = self.item_bank.validate()
        assert not result
        self._assert_has_only_N_matching_problems(result, 1)
        assert len(self.item_bank.selected_children()) == 1

        # Missing problem type should always fail validation
        self.item_bank.capa_type = 'customresponse'
        self._sync_lc_block_from_library()
        self.item_bank.max_count = 1
        result = self.item_bank.validate()
        assert not result
        # Validation fails due to at least one warning/message
        assert result.summary
        assert StudioValidationMessage.WARNING == result.summary.type
        assert 'There are no problems in the specified library of type customresponse' in result.summary.text
        assert len(self.item_bank.selected_children()) == 0

        # -1 selects all blocks from the library.
        self._sync_lc_block_from_library()
        self.item_bank.max_count = -1
        assert self.item_bank.validate()
        assert len(self.item_bank.selected_children()) == len(self.item_bank.children)

    def test_overlimit_blocks_chosen_randomly(self):
        """
        Tests that blocks to remove from selected children are chosen
        randomly when len(selected) > max_count.
        """
        blocks_seen = set()
        total_tries, max_tries = 0, 100

        self._bind_course_block(self.item_bank)

        # Eventually, we should see every child block selected
        while len(blocks_seen) != len(self.items):
            self._change_count_and_reselect_children(len(self.items))
            # Now set the number of selections to 1
            selected = self._change_count_and_reselect_children(1)
            blocks_seen.update(selected)
            total_tries += 1
            if total_tries >= max_tries:
                assert False, "Max tries exceeded before seeing all blocks."
                break

    def _change_count_and_reselect_children(self, count):
        """
        Helper method that changes the max_count of self.item_bank, reselects
        children, and asserts that the number of selected children equals the count provided.
        """
        self.item_bank.max_count = count
        selected = self.item_bank.get_child_blocks()
        assert len(selected) == count
        return selected

    @ddt.data(
        # User resets selected children with reset button on content block
        (True, 8),
        # User resets selected children without reset button on content block
        (False, 8),
        # User resets selected children with reset button on content block when all library blocks should be selected.
        (True, -1),
    )
    @ddt.unpack
    def test_reset_selected_children_capa_blocks(self, allow_resetting_children, max_count):
        """
        Tests that the `reset_selected_children` method of a content block resets only
        XBlocks that have a `reset_problem` attribute when `allow_resetting_children` is True

        This test block has 4 HTML XBlocks and 4 Problem XBlocks. Therefore, if we ensure
        that the `reset_problem` has been called len(self.problem_types) times, then
        it means that this is working correctly
        """
        self.item_bank.allow_resetting_children = allow_resetting_children
        self.item_bank.max_count = max_count
        # Add some capa blocks
        self._add_problems_to_library()
        self._sync_lc_block_from_library(upgrade_to_latest=True)
        # Mock the student view to return an empty dict to be returned as response
        self.item_bank.student_view = MagicMock()
        self.item_bank.student_view.return_value.content = {}

        with patch.object(ProblemBlock, 'reset_problem', return_value={'success': True}) as reset_problem:
            response = self.item_bank.reset_selected_children(None, None)

        if allow_resetting_children:
            self.item_bank.student_view.assert_called_once_with({})
            assert reset_problem.call_count == len(self.problem_types)
            assert response.status_code == status.HTTP_200_OK
            assert response.content_type == "text/html"
            assert response.body == b"{}"
        else:
            reset_problem.assert_not_called()
            assert response.status_code == status.HTTP_400_BAD_REQUEST


search_index_mock = Mock(spec=SearchEngine)  # pylint: disable=invalid-name


@patch(
    'xmodule.modulestore.split_mongo.caching_descriptor_system.CachingDescriptorSystem.render', VanillaRuntime.render
)
@patch('xmodule.html_block.HtmlBlock.author_view', dummy_render, create=True)
@patch('xmodule.x_module.DescriptorSystem.applicable_aside_types', lambda self, block: [])
class TestItemBankRender(ItemBankTestMixin):
    """
    Rendering unit tests for ItemBankBlock
    """

    def setUp(self):
        super().setUp()

    def test_preview_view(self):
        """ Test preview view rendering """
        self._bind_course_block(self.item_bank)
        rendered = self.item_bank.render(AUTHOR_VIEW, {'root_xblock': self.item_bank})
        assert 'Hello world from block 1' in rendered.content

    def test_author_view(self):
        """ Test author view rendering """
        self._bind_course_block(self.item_bank)
        rendered = self.item_bank.render(AUTHOR_VIEW, {})
        assert '' == rendered.content
        # content should be empty
        assert 'LibraryContentAuthorView' == rendered.js_init_fn
        # but some js initialization should happen


class TestItemBankAnalytics(ItemBankTestMixin):
    """
    Test analytics features of ItemBankBlock
    """

    def setUp(self):
        super().setUp()
        self.publisher = Mock()
        self._bind_course_block(self.item_bank)
        self.item_bank.runtime.publish = self.publisher

    def _assert_event_was_published(self, event_type):
        """
        Check that a LegacyLibraryContentBlock analytics event was published by self.item_bank.
        """
        assert self.publisher.called
        assert len(self.publisher.call_args[0]) == 3  # pylint:disable=unsubscriptable-object
        _, event_name, event_data = self.publisher.call_args[0]  # pylint:disable=unsubscriptable-object
        assert event_name == f'edx.librarycontentblock.content.{event_type}'
        assert event_data['location'] == str(self.item_bank.location)
        return event_data

    def test_assigned_event(self):
        """
        Test the "assigned" event emitted when a student is assigned specific blocks.
        """
        # In the beginning was the lc_block and it assigned one child to the student:
        child = self.item_bank.get_child_blocks()[0]
        child_lib_location, child_lib_version = self.store.get_block_original_usage(child.location)
        assert isinstance(child_lib_version, ObjectId)
        event_data = self._assert_event_was_published("assigned")
        block_info = {
            "usage_key": str(child.location),
            "original_usage_key": str(child_lib_location),
            "original_usage_version": str(child_lib_version),
            "descendants": [],
        }
        assert event_data ==\
               {'location': str(self.item_bank.location),
                'added': [block_info],
                'result': [block_info],
                'previous_count': 0, 'max_count': 1}
        self.publisher.reset_mock()

        # Now increase max_count so that one more child will be added:
        self.item_bank.max_count = 2
        children = self.item_bank.get_child_blocks()
        assert len(children) == 2
        child, new_child = children if children[0].location == child.location else reversed(children)
        event_data = self._assert_event_was_published("assigned")
        assert event_data['added'][0]['usage_key'] == str(new_child.location)
        assert len(event_data['result']) == 2
        assert event_data['previous_count'] == 1
        assert event_data['max_count'] == 2

    def test_assigned_event_published(self):
        """
        Same as test_assigned_event but uses the published branch
        """
        self.store.publish(self.course.location, self.user_id)
        with self.store.branch_setting(ModuleStoreEnum.Branch.published_only):
            self.item_bank = self.store.get_item(self.item_bank.location)
            self._bind_course_block(self.item_bank)
            self.item_bank.runtime.publish = self.publisher
            self.test_assigned_event()

    def test_assigned_descendants(self):
        """
        Test the "assigned" event emitted includes descendant block information.
        """
        # Replace the blocks in the library with a block that has descendants:
        with self.store.bulk_operations(self.library.location.library_key):
            self.library.children = []
            main_vertical = self.make_block("vertical", self.library)
            inner_vertical = self.make_block("vertical", main_vertical)
            html_block = self.make_block("html", inner_vertical)
            problem_block = self.make_block("problem", inner_vertical)

        # Reload lc_block and set it up for a student:
        self._sync_lc_block_from_library(upgrade_to_latest=True)
        self._bind_course_block(self.item_bank)
        self.item_bank.runtime.publish = self.publisher

        # Get the keys of each of our blocks, as they appear in the course:
        course_usage_main_vertical = self.item_bank.children[0]
        course_usage_inner_vertical = self.store.get_item(course_usage_main_vertical).children[0]
        inner_vertical_in_course = self.store.get_item(course_usage_inner_vertical)
        course_usage_html = inner_vertical_in_course.children[0]
        course_usage_problem = inner_vertical_in_course.children[1]

        # Trigger a publish event:
        self.item_bank.get_child_blocks()
        event_data = self._assert_event_was_published("assigned")

        for block_list in (event_data["added"], event_data["result"]):
            assert len(block_list) == 1
            # main_vertical is the only root block added, and is the only result.
            assert block_list[0]['usage_key'] == str(course_usage_main_vertical)

            # Check that "descendants" is a flat, unordered list of all of main_vertical's descendants:
            descendants_expected = (
                (inner_vertical.location, course_usage_inner_vertical),
                (html_block.location, course_usage_html),
                (problem_block.location, course_usage_problem),
            )
            descendant_data_expected = {}
            for lib_key, course_usage_key in descendants_expected:
                descendant_data_expected[str(course_usage_key)] = {
                    "usage_key": str(course_usage_key),
                    "original_usage_key": str(lib_key),
                    "original_usage_version": str(self.store.get_block_original_usage(course_usage_key)[1]),
                }
            assert len(block_list[0]['descendants']) == len(descendant_data_expected)
            for descendant in block_list[0]["descendants"]:
                assert descendant == descendant_data_expected.get(descendant['usage_key'])

    def test_removed_overlimit(self):
        """
        Test the "removed" event emitted when we un-assign blocks previously assigned to a student.
        We go from one blocks assigned to none because max_count has been decreased.
        """
        # Decrease max_count to 1, causing the block to be overlimit:
        self.item_bank.get_child_blocks()  # This line is needed in the test environment or the change has no effect
        self.publisher.reset_mock()  # Clear the "assigned" event that was just published.
        self.item_bank.max_count = 0

        # Check that the event says that one block was removed, leaving no blocks left:
        children = self.item_bank.get_child_blocks()
        assert len(children) == 0
        event_data = self._assert_event_was_published("removed")
        assert len(event_data['removed']) == 1
        assert event_data['result'] == []
        assert event_data['reason'] == 'overlimit'

    def test_removed_invalid(self):
        """
        Test the "removed" event emitted when we un-assign blocks previously assigned to a student.
        We go from two blocks assigned, to one because the others have been deleted from the library.
        """

        # Start by assigning two blocks to the student:
        self.item_bank.get_child_blocks()  # This line is needed in the test environment or the change has no effect
        self.item_bank.max_count = 2
        initial_blocks_assigned = self.item_bank.get_child_blocks()
        assert len(initial_blocks_assigned) == 2
        self.publisher.reset_mock()  # Clear the "assigned" event that was just published.
        # Now make sure that one of the assigned blocks will have to be un-assigned.
        # To cause an "invalid" event, we delete all blocks from the content library
        # except for one of the two already assigned to the student:

        keep_block_key = initial_blocks_assigned[0].location
        keep_block_lib_usage_key, keep_block_lib_version = self.store.get_block_original_usage(keep_block_key)
        assert keep_block_lib_usage_key is not None
        deleted_block_key = initial_blocks_assigned[1].location
        self.library.children = [keep_block_lib_usage_key]
        self.store.update_item(self.library, self.user_id)
        self.store.update_item(self.item_bank, self.user_id)
        old_selected = self.item_bank.selected
        self._sync_lc_block_from_library(upgrade_to_latest=True)
        self.item_bank.selected = old_selected
        self.item_bank.runtime.publish = self.publisher

        # Check that the event says that one block was removed, leaving one block left:
        children = self.item_bank.get_child_blocks()
        assert len(children) == 1
        event_data = self._assert_event_was_published("removed")
        assert event_data['removed'] ==\
               [{'usage_key': str(deleted_block_key),
                 'original_usage_key': None,
                 'original_usage_version': None,
                 'descendants': []}]
        assert event_data['result'] ==\
               [{'usage_key': str(keep_block_key),
                 'original_usage_key': str(keep_block_lib_usage_key),
                 'original_usage_version': str(keep_block_lib_version), 'descendants': []}]
        assert event_data['reason'] == 'invalid'
