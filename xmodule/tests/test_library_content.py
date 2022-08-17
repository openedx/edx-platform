"""
Basic unit tests for LibraryContentBlock

Higher-level tests are in `cms/djangoapps/contentstore/tests/test_libraries.py`.
"""
from unittest.mock import MagicMock, Mock, patch
import ddt

from bson.objectid import ObjectId
from fs.memoryfs import MemoryFS
from lxml import etree
from search.search_engine_base import SearchEngine
from web_fragments.fragment import Fragment
from xblock.runtime import Runtime as VanillaRuntime
from rest_framework import status

from xmodule.library_content_module import ANY_CAPA_TYPE_VALUE, LibraryContentBlock
from xmodule.library_tools import LibraryToolsService
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.factories import CourseFactory, LibraryFactory
from xmodule.modulestore.tests.utils import MixedSplitTestCase
from xmodule.tests import get_test_system
from xmodule.validation import StudioValidationMessage
from xmodule.x_module import AUTHOR_VIEW
from xmodule.capa_module import ProblemBlock

from .test_course_module import DummySystem as TestImportSystem

dummy_render = lambda block, _: Fragment(block.data)  # pylint: disable=invalid-name


class LibraryContentTest(MixedSplitTestCase):
    """
    Base class for tests of LibraryContentBlock (library_content_block.py)
    """

    def setUp(self):
        super().setUp()

        self.tools = LibraryToolsService(self.store, self.user_id)
        self.library = LibraryFactory.create(modulestore=self.store)
        self.lib_blocks = [
            self.make_block("html", self.library, data=f"Hello world from block {i}")
            for i in range(1, 5)
        ]
        self.course = CourseFactory.create(modulestore=self.store)
        self.chapter = self.make_block("chapter", self.course)
        self.sequential = self.make_block("sequential", self.chapter)
        self.vertical = self.make_block("vertical", self.sequential)
        self.lc_block = self.make_block(
            "library_content",
            self.vertical,
            max_count=1,
            source_library_id=str(self.library.location.library_key)
        )

    def _bind_course_module(self, module):
        """
        Bind a module (part of self.course) so we can access student-specific data.
        """
        module_system = get_test_system(course_id=module.location.course_key)
        module_system.descriptor_runtime = module.runtime._descriptor_system  # pylint: disable=protected-access
        module_system._services['library_tools'] = self.tools  # pylint: disable=protected-access

        def get_module(descriptor):
            """Mocks module_system get_module function"""
            sub_module_system = get_test_system(course_id=module.location.course_key)
            sub_module_system.get_module = get_module
            sub_module_system.descriptor_runtime = descriptor._runtime  # pylint: disable=protected-access
            descriptor.bind_for_student(sub_module_system, self.user_id)
            return descriptor

        module_system.get_module = get_module
        module.xmodule_runtime = module_system


class TestLibraryContentExportImport(LibraryContentTest):
    """
    Export and import tests for LibraryContentBlock
    """
    def setUp(self):
        super().setUp()

        # Children will only set after calling this.
        self.lc_block.refresh_children()
        self.lc_block = self.store.get_item(self.lc_block.location)

        self.expected_olx = (
            '<library_content display_name="{block.display_name}" max_count="{block.max_count}"'
            ' source_library_id="{block.source_library_id}" source_library_version="{block.source_library_version}">\n'
            '  <html url_name="{block.children[0].block_id}"/>\n'
            '  <html url_name="{block.children[1].block_id}"/>\n'
            '  <html url_name="{block.children[2].block_id}"/>\n'
            '  <html url_name="{block.children[3].block_id}"/>\n'
            '</library_content>\n'
        ).format(
            block=self.lc_block,
        )

        # Set the virtual FS to export the olx to.
        self.export_fs = MemoryFS()
        self.lc_block.runtime._descriptor_system.export_fs = self.export_fs  # pylint: disable=protected-access

        # Prepare runtime for the import.
        self.runtime = TestImportSystem(load_error_modules=True, course_id=self.lc_block.location.course_key)
        self.runtime.resources_fs = self.export_fs
        self.id_generator = Mock()

        # Export the olx.
        node = etree.Element("unknown_root")
        self.lc_block.add_xml_to_node(node)

    def _verify_xblock_properties(self, imported_lc_block):
        """
        Check the new XBlock has the same properties as the old one.
        """
        assert imported_lc_block.display_name == self.lc_block.display_name
        assert imported_lc_block.source_library_id == self.lc_block.source_library_id
        assert imported_lc_block.source_library_version == self.lc_block.source_library_version
        assert imported_lc_block.mode == self.lc_block.mode
        assert imported_lc_block.max_count == self.lc_block.max_count
        assert imported_lc_block.capa_type == self.lc_block.capa_type
        assert len(imported_lc_block.children) == len(self.lc_block.children)
        assert imported_lc_block.children == self.lc_block.children

    def test_xml_export_import_cycle(self):
        """
        Test the export-import cycle.
        """
        # Read back the olx.
        with self.export_fs.open('{dir}/{file_name}.xml'.format(
            dir=self.lc_block.scope_ids.usage_id.block_type,
            file_name=self.lc_block.scope_ids.usage_id.block_id
        )) as f:
            exported_olx = f.read()

        # And compare.
        assert exported_olx == self.expected_olx

        # Now import it.
        olx_element = etree.fromstring(exported_olx)
        imported_lc_block = LibraryContentBlock.parse_xml(olx_element, self.runtime, None, self.id_generator)

        self._verify_xblock_properties(imported_lc_block)

    def test_xml_import_with_comments(self):
        """
        Test that XML comments within LibraryContentBlock are ignored during the import.
        """
        olx_with_comments = (
            '<!-- Comment -->\n'
            '<library_content display_name="{block.display_name}" max_count="{block.max_count}"'
            ' source_library_id="{block.source_library_id}" source_library_version="{block.source_library_version}">\n'
            '<!-- Comment -->\n'
            '  <html url_name="{block.children[0].block_id}"/>\n'
            '  <html url_name="{block.children[1].block_id}"/>\n'
            '  <html url_name="{block.children[2].block_id}"/>\n'
            '  <html url_name="{block.children[3].block_id}"/>\n'
            '</library_content>\n'
        ).format(
            block=self.lc_block,
        )

        # Import the olx.
        olx_element = etree.fromstring(olx_with_comments)
        imported_lc_block = LibraryContentBlock.parse_xml(olx_element, self.runtime, None, self.id_generator)

        self._verify_xblock_properties(imported_lc_block)


@ddt.ddt
class LibraryContentBlockTestMixin:
    """
    Basic unit tests for LibraryContentBlock
    """
    problem_types = [
        ["multiplechoiceresponse"], ["optionresponse"], ["optionresponse", "coderesponse"],
        ["coderesponse", "optionresponse"]
    ]

    problem_type_lookup = {}

    def _get_capa_problem_type_xml(self, *args):
        """ Helper function to create empty CAPA problem definition """
        problem = "<problem>"
        for problem_type in args:
            problem += "<{problem_type}></{problem_type}>".format(problem_type=problem_type)
        problem += "</problem>"
        return problem

    def _create_capa_problems(self):
        """
        Helper function to create a set of capa problems to test against.

        Creates four blocks total.
        """
        self.problem_type_lookup = {}
        for problem_type in self.problem_types:
            block = self.make_block("problem", self.library, data=self._get_capa_problem_type_xml(*problem_type))
            self.problem_type_lookup[block.location] = problem_type

    def test_lib_content_block(self):
        """
        Test that blocks from a library are copied and added as children
        """
        # Check that the LibraryContent block has no children initially
        # Normally the children get added when the "source_libraries" setting
        # is updated, but the way we do it through a factory doesn't do that.
        assert len(self.lc_block.children) == 0
        # Update the LibraryContent module:
        self.lc_block.refresh_children()
        self.lc_block = self.store.get_item(self.lc_block.location)
        # Check that all blocks from the library are now children of the block:
        assert len(self.lc_block.children) == len(self.lib_blocks)

    def test_children_seen_by_a_user(self):
        """
        Test that each student sees only one block as a child of the LibraryContent block.
        """
        self.lc_block.refresh_children()
        self.lc_block = self.store.get_item(self.lc_block.location)
        self._bind_course_module(self.lc_block)
        # Make sure the runtime knows that the block's children vary per-user:
        assert self.lc_block.has_dynamic_children()

        assert len(self.lc_block.children) == len(self.lib_blocks)

        # Check how many children each user will see:
        assert len(self.lc_block.get_child_descriptors()) == 1
        # Check that get_content_titles() doesn't return titles for hidden/unused children
        assert len(self.lc_block.get_content_titles()) == 1

    def test_validation_of_course_libraries(self):
        """
        Test that the validation method of LibraryContent blocks can validate
        the source_library setting.
        """
        # When source_library_id is blank, the validation summary should say this block needs to be configured:
        self.lc_block.source_library_id = ""
        result = self.lc_block.validate()
        assert not result
        # Validation fails due to at least one warning/message
        assert result.summary
        assert StudioValidationMessage.NOT_CONFIGURED == result.summary.type

        # When source_library_id references a non-existent library, we should get an error:
        self.lc_block.source_library_id = "library-v1:BAD+WOLF"
        result = self.lc_block.validate()
        assert not result
        # Validation fails due to at least one warning/message
        assert result.summary
        assert StudioValidationMessage.ERROR == result.summary.type
        assert 'invalid' in result.summary.text

        # When source_library_id is set but the block needs to be updated, the summary should say so:
        self.lc_block.source_library_id = str(self.library.location.library_key)
        result = self.lc_block.validate()
        assert not result
        # Validation fails due to at least one warning/message
        assert result.summary
        assert StudioValidationMessage.WARNING == result.summary.type
        assert 'out of date' in result.summary.text

        # Now if we update the block, all validation should pass:
        self.lc_block.refresh_children()
        assert self.lc_block.validate()

    def test_validation_of_matching_blocks(self):
        """
        Test that the validation method of LibraryContent blocks can warn
        the user about problems with other settings (max_count and capa_type).
        """
        # Set max_count to higher value than exists in library
        self.lc_block.max_count = 50
        # In the normal studio editing process, editor_saved() calls refresh_children at this point
        self.lc_block.refresh_children()
        result = self.lc_block.validate()
        assert not result
        # Validation fails due to at least one warning/message
        assert result.summary
        assert StudioValidationMessage.WARNING == result.summary.type
        assert 'only 4 matching problems' in result.summary.text

        # Add some capa problems so we can check problem type validation messages
        self.lc_block.max_count = 1
        self._create_capa_problems()
        self.lc_block.refresh_children()
        assert self.lc_block.validate()

        # Existing problem type should pass validation
        self.lc_block.max_count = 1
        self.lc_block.capa_type = 'multiplechoiceresponse'
        self.lc_block.refresh_children()
        assert self.lc_block.validate()

        # ... unless requested more blocks than exists in library
        self.lc_block.max_count = 10
        self.lc_block.capa_type = 'multiplechoiceresponse'
        self.lc_block.refresh_children()
        result = self.lc_block.validate()
        assert not result
        # Validation fails due to at least one warning/message
        assert result.summary
        assert StudioValidationMessage.WARNING == result.summary.type
        assert 'only 1 matching problem' in result.summary.text

        # Missing problem type should always fail validation
        self.lc_block.max_count = 1
        self.lc_block.capa_type = 'customresponse'
        self.lc_block.refresh_children()
        result = self.lc_block.validate()
        assert not result
        # Validation fails due to at least one warning/message
        assert result.summary
        assert StudioValidationMessage.WARNING == result.summary.type
        assert 'no matching problem types' in result.summary.text

    def test_capa_type_filtering(self):
        """
        Test that the capa type filter is actually filtering children
        """
        self._create_capa_problems()
        assert len(self.lc_block.children) == 0
        # precondition check
        self.lc_block.capa_type = "multiplechoiceresponse"
        self.lc_block.refresh_children()
        assert len(self.lc_block.children) == 1

        self.lc_block.capa_type = "optionresponse"
        self.lc_block.refresh_children()
        assert len(self.lc_block.children) == 3

        self.lc_block.capa_type = "coderesponse"
        self.lc_block.refresh_children()
        assert len(self.lc_block.children) == 2

        self.lc_block.capa_type = "customresponse"
        self.lc_block.refresh_children()
        assert len(self.lc_block.children) == 0

        self.lc_block.capa_type = ANY_CAPA_TYPE_VALUE
        self.lc_block.refresh_children()
        assert len(self.lc_block.children) == (len(self.lib_blocks) + 4)

    def test_non_editable_settings(self):
        """
        Test the settings that are marked as "non-editable".
        """
        non_editable_metadata_fields = self.lc_block.non_editable_metadata_fields
        assert LibraryContentBlock.mode in non_editable_metadata_fields
        assert LibraryContentBlock.display_name not in non_editable_metadata_fields

    def test_overlimit_blocks_chosen_randomly(self):
        """
        Tests that blocks to remove from selected children are chosen
        randomly when len(selected) > max_count.
        """
        blocks_seen = set()
        total_tries, max_tries = 0, 100

        self.lc_block.refresh_children()
        self.lc_block = self.store.get_item(self.lc_block.location)
        self._bind_course_module(self.lc_block)

        # Eventually, we should see every child block selected
        while len(blocks_seen) != len(self.lib_blocks):
            self._change_count_and_refresh_children(len(self.lib_blocks))
            # Now set the number of selections to 1
            selected = self._change_count_and_refresh_children(1)
            blocks_seen.update(selected)
            total_tries += 1
            if total_tries >= max_tries:
                assert False, "Max tries exceeded before seeing all blocks."
                break

    def _change_count_and_refresh_children(self, count):
        """
        Helper method that changes the max_count of self.lc_block, refreshes
        children, and asserts that the number of selected children equals the count provided.
        """
        self.lc_block.max_count = count
        selected = self.lc_block.get_child_descriptors()
        assert len(selected) == count
        return selected

    @ddt.data(
        # User resets selected children with reset button on content block
        (True, 8),
        # User resets selected children without reset button on content block
        (False, 8),
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
        self.lc_block.allow_resetting_children = allow_resetting_children
        self.lc_block.max_count = max_count
        # Add some capa blocks
        self._create_capa_problems()
        self.lc_block.refresh_children()
        self.lc_block = self.store.get_item(self.lc_block.location)
        # Mock the student view to return an empty dict to be returned as response
        self.lc_block.student_view = MagicMock()
        self.lc_block.student_view.return_value.content = {}

        with patch.object(ProblemBlock, 'reset_problem', return_value={'success': True}) as reset_problem:
            response = self.lc_block.reset_selected_children(None, None)

        if allow_resetting_children:
            self.lc_block.student_view.assert_called_once_with({})
            assert reset_problem.call_count == len(self.problem_types)
            assert response.status_code == status.HTTP_200_OK
            assert response.content_type == "text/html"
            assert response.body == b"{}"
        else:
            reset_problem.assert_not_called()
            assert response.status_code == status.HTTP_400_BAD_REQUEST


@patch('xmodule.library_tools.SearchEngine.get_search_engine', Mock(return_value=None, autospec=True))
class TestLibraryContentBlockNoSearchIndex(LibraryContentBlockTestMixin, LibraryContentTest):
    """
    Tests for library container when no search index is available.
    Tests fallback low-level CAPA problem introspection
    """
    pass  # pylint:disable=unnecessary-pass


search_index_mock = Mock(spec=SearchEngine)  # pylint: disable=invalid-name


@patch('xmodule.library_tools.SearchEngine.get_search_engine', Mock(return_value=search_index_mock, autospec=True))
class TestLibraryContentBlockWithSearchIndex(LibraryContentBlockTestMixin, LibraryContentTest):
    """
    Tests for library container with mocked search engine response.
    """

    def _get_search_response(self, field_dictionary=None):
        """ Mocks search response as returned by search engine """
        target_type = field_dictionary.get('problem_types')
        matched_block_locations = [
            key for key, problem_types in
            self.problem_type_lookup.items() if target_type in problem_types
        ]
        return {
            'results': [
                {'data': {'id': str(location)}} for location in matched_block_locations
            ]
        }

    def setUp(self):
        """ Sets up search engine mock """
        super().setUp()
        search_index_mock.search = Mock(side_effect=self._get_search_response)


@patch(
    'xmodule.modulestore.split_mongo.caching_descriptor_system.CachingDescriptorSystem.render', VanillaRuntime.render
)
@patch('xmodule.html_module.HtmlBlock.author_view', dummy_render, create=True)
@patch('xmodule.x_module.DescriptorSystem.applicable_aside_types', lambda self, block: [])
class TestLibraryContentRender(LibraryContentTest):
    """
    Rendering unit tests for LibraryContentBlock
    """

    def test_preview_view(self):
        """ Test preview view rendering """
        self.lc_block.refresh_children()
        self.lc_block = self.store.get_item(self.lc_block.location)
        assert len(self.lc_block.children) == len(self.lib_blocks)
        self._bind_course_module(self.lc_block)
        rendered = self.lc_block.render(AUTHOR_VIEW, {'root_xblock': self.lc_block})
        assert 'Hello world from block 1' in rendered.content

    def test_author_view(self):
        """ Test author view rendering """
        self.lc_block.refresh_children()
        self.lc_block = self.store.get_item(self.lc_block.location)
        assert len(self.lc_block.children) == len(self.lib_blocks)
        self._bind_course_module(self.lc_block)
        rendered = self.lc_block.render(AUTHOR_VIEW, {})
        assert '' == rendered.content
        # content should be empty
        assert 'LibraryContentAuthorView' == rendered.js_init_fn
        # but some js initialization should happen


class TestLibraryContentAnalytics(LibraryContentTest):
    """
    Test analytics features of LibraryContentBlock
    """

    def setUp(self):
        super().setUp()
        self.publisher = Mock()
        self.lc_block.refresh_children()
        self.lc_block = self.store.get_item(self.lc_block.location)
        self._bind_course_module(self.lc_block)
        self.lc_block.xmodule_runtime.publish = self.publisher

    def _assert_event_was_published(self, event_type):
        """
        Check that a LibraryContentBlock analytics event was published by self.lc_block.
        """
        assert self.publisher.called
        assert len(self.publisher.call_args[0]) == 3  # pylint:disable=unsubscriptable-object
        _, event_name, event_data = self.publisher.call_args[0]  # pylint:disable=unsubscriptable-object
        assert event_name == f'edx.librarycontentblock.content.{event_type}'
        assert event_data['location'] == str(self.lc_block.location)
        return event_data

    def test_assigned_event(self):
        """
        Test the "assigned" event emitted when a student is assigned specific blocks.
        """
        # In the beginning was the lc_block and it assigned one child to the student:
        child = self.lc_block.get_child_descriptors()[0]
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
               {'location': str(self.lc_block.location),
                'added': [block_info],
                'result': [block_info],
                'previous_count': 0, 'max_count': 1}
        self.publisher.reset_mock()

        # Now increase max_count so that one more child will be added:
        self.lc_block.max_count = 2
        children = self.lc_block.get_child_descriptors()
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
            self.lc_block = self.store.get_item(self.lc_block.location)
            self._bind_course_module(self.lc_block)
            self.lc_block.xmodule_runtime.publish = self.publisher
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
            self.lc_block.refresh_children()

        # Reload lc_block and set it up for a student:
        self.lc_block = self.store.get_item(self.lc_block.location)
        self._bind_course_module(self.lc_block)
        self.lc_block.xmodule_runtime.publish = self.publisher

        # Get the keys of each of our blocks, as they appear in the course:
        course_usage_main_vertical = self.lc_block.children[0]
        course_usage_inner_vertical = self.store.get_item(course_usage_main_vertical).children[0]
        inner_vertical_in_course = self.store.get_item(course_usage_inner_vertical)
        course_usage_html = inner_vertical_in_course.children[0]
        course_usage_problem = inner_vertical_in_course.children[1]

        # Trigger a publish event:
        self.lc_block.get_child_descriptors()
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
        self.lc_block.get_child_descriptors()  # This line is needed in the test environment or the change has no effect
        self.publisher.reset_mock()  # Clear the "assigned" event that was just published.
        self.lc_block.max_count = 0

        # Check that the event says that one block was removed, leaving no blocks left:
        children = self.lc_block.get_child_descriptors()
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
        self.lc_block.get_child_descriptors()  # This line is needed in the test environment or the change has no effect
        self.lc_block.max_count = 2
        initial_blocks_assigned = self.lc_block.get_child_descriptors()
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
        self.lc_block.refresh_children()

        # Check that the event says that one block was removed, leaving one block left:
        children = self.lc_block.get_child_descriptors()
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
