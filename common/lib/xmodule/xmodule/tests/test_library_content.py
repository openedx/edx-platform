# -*- coding: utf-8 -*-
"""
Basic unit tests for LibraryContentModule

Higher-level tests are in `cms/djangoapps/contentstore/tests/test_libraries.py`.
"""
from random import choice
from string import ascii_lowercase, digits

from bson.objectid import ObjectId
from mock import DEFAULT, Mock, patch

from xblock.fragment import Fragment
from xblock.runtime import Runtime as VanillaRuntime

from xmodule.library_content_module import (
    ANY_CAPA_TYPE_VALUE, AdaptiveLibraryContentModule, LibraryContentDescriptor, LibraryContentModule,
)
from xmodule.library_tools import LibraryToolsService
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.factories import LibraryFactory, CourseFactory
from xmodule.modulestore.tests.utils import MixedSplitTestCase
from xmodule.tests import get_test_system
from xmodule.validation import StudioValidationMessage
from xmodule.x_module import AUTHOR_VIEW
from search.search_engine_base import SearchEngine

dummy_render = lambda block, _: Fragment(block.data)  # pylint: disable=invalid-name


class LibraryContentTest(MixedSplitTestCase):
    """
    Base class for tests of LibraryContentModule (library_content_module.py)
    """
    DEFAULTS = {
        "category": "library_content",
        "module_class": LibraryContentModule,
        "fields": {
            "display_name": "Randomized Content Block",
        },
    }

    def setUp(self):
        super(LibraryContentTest, self).setUp()

        self.tools = LibraryToolsService(self.store)
        self.library = LibraryFactory.create(modulestore=self.store)
        self.lib_blocks = [
            self.make_block("html", self.library, data="Hello world from block {}".format(i))
            for i in range(1, 5)
        ]
        self.course = CourseFactory.create(modulestore=self.store)
        self.chapter = self.make_block("chapter", self.course)
        self.sequential = self.make_block("sequential", self.chapter)
        self.vertical = self.make_block("vertical", self.sequential)
        self.lc_block = self.make_block(
            self.DEFAULTS["category"],
            self.vertical,
            max_count=1,
            source_library_id=unicode(self.library.location.library_key)
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


class AdaptiveLibraryContentTest(LibraryContentTest):
    """
    Base class for tests of AdaptiveLibraryContentModule (library_content_module.py)
    """
    DEFAULTS = {
        "category": "adaptive_library_content",
        "module_class": AdaptiveLibraryContentModule,
        "fields": {
            "display_name": "Adaptive Content Block",
        },
    }


class LibraryContentModuleTestMixin(object):
    """
    Basic unit tests for LibraryContentModule
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

    def test_defaults(self):
        """
        Test that block defaults match expected values.
        """
        category = self.lc_block.category
        self.assertEqual(category, self.DEFAULTS["category"])

        module_class = self.lc_block.module_class
        self.assertEqual(module_class, self.DEFAULTS["module_class"])

        display_name = self.lc_block.fields["display_name"]
        self.assertEqual(display_name.default, self.DEFAULTS["fields"]["display_name"])

    def test_lib_content_block(self):
        """
        Test that blocks from a library are copied and added as children
        """
        # Check that the LibraryContent block has no children initially
        # Normally the children get added when the "source_libraries" setting
        # is updated, but the way we do it through a factory doesn't do that.
        self.assertEqual(len(self.lc_block.children), 0)
        # Update the LibraryContent module:
        self.lc_block.refresh_children()
        self.lc_block = self.store.get_item(self.lc_block.location)
        # Check that all blocks from the library are now children of the block:
        self.assertEqual(len(self.lc_block.children), len(self.lib_blocks))

    def test_children_seen_by_a_user(self):
        """
        Test that each student sees only one block as a child of the LibraryContent block.
        """
        self.lc_block.refresh_children()
        self.lc_block = self.store.get_item(self.lc_block.location)
        self._bind_course_module(self.lc_block)
        # Make sure the runtime knows that the block's children vary per-user:
        self.assertTrue(self.lc_block.has_dynamic_children())

        self.assertEqual(len(self.lc_block.children), len(self.lib_blocks))

        # Check how many children each user will see:
        self.assertEqual(len(self.lc_block.get_child_descriptors()), 1)
        # Check that get_content_titles() doesn't return titles for hidden/unused children
        self.assertEqual(len(self.lc_block.get_content_titles()), 1)

    def test_validation_of_course_libraries(self):
        """
        Test that the validation method of LibraryContent blocks can validate
        the source_library setting.
        """
        # When source_library_id is blank, the validation summary should say this block needs to be configured:
        self.lc_block.source_library_id = ""
        result = self.lc_block.validate()
        self.assertFalse(result)  # Validation fails due to at least one warning/message
        self.assertTrue(result.summary)
        self.assertEqual(StudioValidationMessage.NOT_CONFIGURED, result.summary.type)

        # When source_library_id references a non-existent library, we should get an error:
        self.lc_block.source_library_id = "library-v1:BAD+WOLF"
        result = self.lc_block.validate()
        self.assertFalse(result)  # Validation fails due to at least one warning/message
        self.assertTrue(result.summary)
        self.assertEqual(StudioValidationMessage.ERROR, result.summary.type)
        self.assertIn("invalid", result.summary.text)

        # When source_library_id is set but the block needs to be updated, the summary should say so:
        self.lc_block.source_library_id = unicode(self.library.location.library_key)
        result = self.lc_block.validate()
        self.assertFalse(result)  # Validation fails due to at least one warning/message
        self.assertTrue(result.summary)
        self.assertEqual(StudioValidationMessage.WARNING, result.summary.type)
        self.assertIn("out of date", result.summary.text)

        # Now if we update the block, all validation should pass:
        self.lc_block.refresh_children()
        self.assertTrue(self.lc_block.validate())

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
        self.assertFalse(result)  # Validation fails due to at least one warning/message
        self.assertTrue(result.summary)
        self.assertEqual(StudioValidationMessage.WARNING, result.summary.type)
        self.assertIn("only 4 matching problems", result.summary.text)

        # Add some capa problems so we can check problem type validation messages
        self.lc_block.max_count = 1
        self._create_capa_problems()
        self.lc_block.refresh_children()
        self.assertTrue(self.lc_block.validate())

        # Existing problem type should pass validation
        self.lc_block.max_count = 1
        self.lc_block.capa_type = 'multiplechoiceresponse'
        self.lc_block.refresh_children()
        self.assertTrue(self.lc_block.validate())

        # ... unless requested more blocks than exists in library
        self.lc_block.max_count = 10
        self.lc_block.capa_type = 'multiplechoiceresponse'
        self.lc_block.refresh_children()
        result = self.lc_block.validate()
        self.assertFalse(result)  # Validation fails due to at least one warning/message
        self.assertTrue(result.summary)
        self.assertEqual(StudioValidationMessage.WARNING, result.summary.type)
        self.assertIn("only 1 matching problem", result.summary.text)

        # Missing problem type should always fail validation
        self.lc_block.max_count = 1
        self.lc_block.capa_type = 'customresponse'
        self.lc_block.refresh_children()
        result = self.lc_block.validate()
        self.assertFalse(result)  # Validation fails due to at least one warning/message
        self.assertTrue(result.summary)
        self.assertEqual(StudioValidationMessage.WARNING, result.summary.type)
        self.assertIn("no matching problem types", result.summary.text)

    def test_capa_type_filtering(self):
        """
        Test that the capa type filter is actually filtering children
        """
        self._create_capa_problems()
        self.assertEqual(len(self.lc_block.children), 0)  # precondition check
        self.lc_block.capa_type = "multiplechoiceresponse"
        self.lc_block.refresh_children()
        self.assertEqual(len(self.lc_block.children), 1)

        self.lc_block.capa_type = "optionresponse"
        self.lc_block.refresh_children()
        self.assertEqual(len(self.lc_block.children), 3)

        self.lc_block.capa_type = "coderesponse"
        self.lc_block.refresh_children()
        self.assertEqual(len(self.lc_block.children), 2)

        self.lc_block.capa_type = "customresponse"
        self.lc_block.refresh_children()
        self.assertEqual(len(self.lc_block.children), 0)

        self.lc_block.capa_type = ANY_CAPA_TYPE_VALUE
        self.lc_block.refresh_children()
        self.assertEqual(len(self.lc_block.children), len(self.lib_blocks) + 4)

    def test_non_editable_settings(self):
        """
        Test the settings that are marked as "non-editable".
        """
        non_editable_metadata_fields = self.lc_block.non_editable_metadata_fields
        self.assertIn(LibraryContentDescriptor.mode, non_editable_metadata_fields)
        self.assertNotIn(LibraryContentDescriptor.display_name, non_editable_metadata_fields)


class AdaptiveLibraryContentModuleTestMixin(LibraryContentModuleTestMixin):
    """
    Basic unit tests for AdaptiveLibraryContentModule
    """
    @patch('xmodule.library_content_module.AdaptiveLearningAPIClient.get_pending_reviews', Mock(return_value=[]))
    def test_children_seen_by_a_user(self):
        """
        Test that each student sees zero child blocks for AdaptiveLibraryContent block by default.
        """
        self.lc_block.refresh_children()
        self.lc_block = self.store.get_item(self.lc_block.location)  # pylint: disable=attribute-defined-outside-init
        self._bind_course_module(self.lc_block)

        # Make sure the runtime knows that the block's children vary per-user:
        self.assertTrue(self.lc_block.has_dynamic_children())

        self.assertEqual(len(self.lc_block.children), len(self.lib_blocks))

        # Check how many children each user will see:
        self.assertEqual(len(self.lc_block.get_child_descriptors()), 0)
        # Check that get_content_titles() doesn't return titles for hidden/unused children
        self.assertEqual(len(self.lc_block.get_content_titles()), 0)

    def test_parent_course(self):
        """
        Test that `parent_course` property uses expected API for obtaining parent course,
        calls it with appropriate arguments, and returns appropriate value.
        """
        self._bind_course_module(self.lc_block)
        module = self.lc_block._xmodule  # pylint: disable=protected-access
        with patch.object(module.runtime.modulestore, 'get_course') as patched_get_course:
            patched_get_course.return_value = self.course
            parent_course = module.parent_course
            self.assertEqual(parent_course, self.course)
            patched_get_course.assert_called_once_with(module.course_id, depth=1)

    def test_parent_unit_id(self):
        """
        Test that `parent_unit_id` property uses expected API for obtaining parent course,
        calls it with appropriate arguments, and returns appropriate value.
        """
        self._bind_course_module(self.lc_block)
        module = self.lc_block._xmodule  # pylint: disable=protected-access
        with patch.object(module, 'get_parent') as patched_get_parent:
            patched_get_parent.return_value = self.vertical
            parent_unit_id = module.parent_unit_id
            expected_parent_unit_id = self.vertical.scope_ids.usage_id.block_id
            self.assertEqual(parent_unit_id, expected_parent_unit_id)
            patched_get_parent.assert_called_once_with()

    def test_current_user_id(self):
        """
        Test that `current_user_id` property uses expected API for obtaining ID of current user,
        calls it with appropriate arguments, and returns appropriate value.
        """
        self._bind_course_module(self.lc_block)
        module = self.lc_block._xmodule  # pylint: disable=protected-access
        with patch.object(self.lc_block, 'get_user_id') as patched_get_user_id:
            patched_get_user_id.return_value = 42
            user_id = module.current_user_id
            self.assertEqual(user_id, 42)
            patched_get_user_id.assert_called_once_with()

    def test_current_user_id_no_user_service(self):
        """
        Test that `current_user_id` property returns `None` if user service is not available.
        """
        self._bind_course_module(self.lc_block)
        module = self.lc_block._xmodule  # pylint: disable=protected-access
        with patch.object(module.runtime, 'service') as patched_service:
            patched_service.return_value = None
            user_id = module.current_user_id
            self.assertIsNone(user_id)

    def test_child_block_ids(self):
        """
        Test that `child_block_ids` property returns correct list containing correct IDs.
        """
        self._bind_course_module(self.lc_block)
        module = self.lc_block._xmodule  # pylint: disable=protected-access
        expected_child_block_ids = [child.block_id for child in module.children]
        self.assertEqual(module.child_block_ids, expected_child_block_ids)

    def test_get_selections_current_user(self):
        """
        Test that `get_selections_current_user` calls method for obtaining list of pending reviews
        for current user, and returns selection appropriate for current block.
        """
        def generate_random_block_id(length):
            """
            Return random block ID of length `length`.
            """
            return ''.join(choice(ascii_lowercase + digits) for dummy in range(length))

        self._bind_course_module(self.lc_block)
        module = self.lc_block._xmodule  # pylint: disable=protected-access
        user_id = module.current_user_id
        children = module.children
        relevant_reviews = [
            {
                'knowledge_node_uid': generate_random_block_id(32),
                'review_question_uid': child.block_id,

            } for child in children
        ]
        irrelevant_reviews = [
            {
                'knowledge_node_uid': generate_random_block_id(32),
                'review_question_uid': generate_random_block_id(20),
            } for dummy in range(5)
        ]
        pending_reviews = relevant_reviews + irrelevant_reviews
        expected_selections = [(c.block_type, c.block_id) for c in children]
        with patch(
            'xmodule.library_content_module.AdaptiveLearningAPIClient.get_pending_reviews'
        ) as patched_get_pending_reviews:
            patched_get_pending_reviews.return_value = pending_reviews
            selections_current_user = module.get_selections_current_user(children)
            self.assertEqual(selections_current_user, expected_selections)
            patched_get_pending_reviews.assert_called_once_with(user_id)

    def test_send_unit_viewed_event(self):
        """
        Test that `send_unit_viewed_event` calls method for notifying external service
        with appropriate arguments.
        """
        self._bind_course_module(self.lc_block)
        module = self.lc_block._xmodule  # pylint: disable=protected-access
        block_id = module.parent_unit_id
        user_id = module.current_user_id
        with patch(
            'xmodule.library_content_module.AdaptiveLearningAPIClient.create_read_event'
        ) as patched_create_read_event:
            module.send_unit_viewed_event()
            patched_create_read_event.assert_called_once_with(block_id, user_id)

    def test_link_current_user_to_children(self):
        """
        Test that `link_current_user_to_children` calls method for linking current user
        to children of adaptive content block with appropriate arguments.
        """
        self._bind_course_module(self.lc_block)
        module = self.lc_block._xmodule  # pylint: disable=protected-access
        block_ids = module.child_block_ids
        user_id = module.current_user_id
        with patch(
            'xmodule.library_content_module.AdaptiveLearningAPIClient.create_knowledge_node_students'
        ) as patched_create:
            module.link_current_user_to_children()
            patched_create.assert_called_once_with(block_ids, user_id)

    def test_send_result_event(self):
        """
        Test that `send_result_event` calls method for notifying external service
        with appropriate arguments.
        """
        self.lc_block.refresh_children()
        self.lc_block = self.store.get_item(self.lc_block.location)  # pylint: disable=attribute-defined-outside-init
        self._bind_course_module(self.lc_block)
        module = self.lc_block._xmodule  # pylint: disable=protected-access
        course = module.parent_course
        block_id = module.child_block_ids[0]
        user_id = module.current_user_id
        result = '100'
        with patch(
            'xmodule.library_content_module.AdaptiveLearningAPIClient'
        ) as patched_class:
            mock_client = Mock(autospec=True)
            patched_class.return_value = mock_client
            AdaptiveLibraryContentModule.send_result_event(course, block_id, user_id, result)
            patched_class.assert_called_once_with(course)
            mock_client.create_result_event.assert_called_once_with(block_id, user_id, result)

    def test_fetch_pending_reviews(self):
        """
        Test that `fetch_pending_reviews` calls method for obtaining pending reviews
        with appropriate arguments, and returns results unchanged.
        """
        self._bind_course_module(self.lc_block)
        module = self.lc_block._xmodule  # pylint: disable=protected-access
        course = module.parent_course
        user_id = module.current_user_id
        expected_pending_reviews = [
            {
                'knowledge_node_uid': 'knowledge-node-{n}'.format(n=n),
                'review_question_uid': 'review-question-{n}'.format(n=n),
            } for n in range(5)
        ]
        with patch(
            'xmodule.library_content_module.AdaptiveLearningAPIClient'
        ) as patched_class:
            mock_client = Mock(autospec=True)
            mock_client.get_pending_reviews.return_value = expected_pending_reviews
            patched_class.return_value = mock_client
            pending_reviews = AdaptiveLibraryContentModule.fetch_pending_reviews(course, user_id)
            self.assertEqual(pending_reviews, expected_pending_reviews)
            patched_class.assert_called_once_with(course)
            mock_client.get_pending_reviews.assert_called_once_with(user_id)

    def test_student_view(self):
        """
        Test that `student_view` notifies external service that parent unit has been viewed,
        and creates links between current user and children of block under test.
        """
        self._bind_course_module(self.lc_block)
        module = self.lc_block._xmodule  # pylint: disable=protected-access
        with patch.multiple(
            module,
            send_unit_viewed_event=DEFAULT,
            link_current_user_to_children=DEFAULT,
            _get_selected_child_blocks=DEFAULT
        ) as patched_methods:
            patched_methods['_get_selected_child_blocks'].return_value = []
            context = {}
            module.student_view(context)
            patched_methods['send_unit_viewed_event'].assert_called_once_with()
            patched_methods['link_current_user_to_children'].assert_called_once_with()


@patch('xmodule.library_tools.SearchEngine.get_search_engine', Mock(return_value=None, autospec=True))
class TestLibraryContentModuleNoSearchIndex(LibraryContentModuleTestMixin, LibraryContentTest):
    """
    Tests for LibraryContentModule when no search index is available.
    Tests fallback low-level CAPA problem introspection
    """
    pass


@patch('xmodule.library_tools.SearchEngine.get_search_engine', Mock(return_value=None, autospec=True))
class TestAdaptiveLibraryContentModuleNoSearchIndex(AdaptiveLibraryContentModuleTestMixin, AdaptiveLibraryContentTest):
    """
    Tests for LibraryContentModule when no search index is available.
    Tests fallback low-level CAPA problem introspection
    """
    pass


search_index_mock = Mock(spec=SearchEngine)  # pylint: disable=invalid-name


class SearchIndexMixin(object):
    """
    Mixin that makes a mocked search available to tests using it.
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
        super(SearchIndexMixin, self).setUp()
        search_index_mock.search = Mock(side_effect=self._get_search_response)


@patch('xmodule.library_tools.SearchEngine.get_search_engine', Mock(return_value=search_index_mock, autospec=True))
class TestLibraryContentModuleWithSearchIndex(
        LibraryContentModuleTestMixin, SearchIndexMixin, LibraryContentTest
):
    """
    Tests for LibraryContentModule with mocked search engine response.
    """
    pass


@patch('xmodule.library_tools.SearchEngine.get_search_engine', Mock(return_value=search_index_mock, autospec=True))
class TestAdaptiveLibraryContentModuleWithSearchIndex(  # pylint: disable=invalid-name
        AdaptiveLibraryContentModuleTestMixin, SearchIndexMixin, AdaptiveLibraryContentTest
):
    """
    Tests for AdaptiveLibraryContentModule with mocked search engine response.
    """
    pass


class LibraryContentRenderMixin(object):
    """
    Mixin for unit tests that check rendering results
    """
    def test_preview_view(self):
        """ Test preview view rendering """
        self.lc_block.refresh_children()
        self.lc_block = self.store.get_item(self.lc_block.location)
        self.assertEqual(len(self.lc_block.children), len(self.lib_blocks))
        self._bind_course_module(self.lc_block)
        rendered = self.lc_block.render(AUTHOR_VIEW, {'root_xblock': self.lc_block})
        self.assertIn("Hello world from block 1", rendered.content)

    def test_author_view(self):
        """ Test author view rendering """
        self.lc_block.refresh_children()
        self.lc_block = self.store.get_item(self.lc_block.location)
        self.assertEqual(len(self.lc_block.children), len(self.lib_blocks))
        self._bind_course_module(self.lc_block)
        rendered = self.lc_block.render(AUTHOR_VIEW, {})
        self.assertEqual("", rendered.content)  # content should be empty
        self.assertEqual("LibraryContentAuthorView", rendered.js_init_fn)  # but some js initialization should happen


@patch(
    'xmodule.modulestore.split_mongo.caching_descriptor_system.CachingDescriptorSystem.render', VanillaRuntime.render
)
@patch('xmodule.html_module.HtmlModule.author_view', dummy_render, create=True)
@patch('xmodule.x_module.DescriptorSystem.applicable_aside_types', lambda self, block: [])
class TestLibraryContentRender(LibraryContentRenderMixin, LibraryContentTest):
    """
    Rendering unit tests for LibraryContentModule
    """
    pass


@patch(
    'xmodule.modulestore.split_mongo.caching_descriptor_system.CachingDescriptorSystem.render', VanillaRuntime.render
)
@patch('xmodule.html_module.HtmlModule.author_view', dummy_render, create=True)
@patch('xmodule.x_module.DescriptorSystem.applicable_aside_types', lambda self, block: [])
class TestAdaptiveLibraryContentRender(LibraryContentRenderMixin, AdaptiveLibraryContentTest):
    """
    Rendering unit tests for AdaptiveLibraryContentModule
    """
    pass


class LibraryContentAnalyticsMixin(object):
    """
    Mixin for testing analytics features of library content modules
    """
    def setUp(self):
        super(LibraryContentAnalyticsMixin, self).setUp()
        self.publisher = Mock()
        self.lc_block.refresh_children()
        self.lc_block = self.store.get_item(self.lc_block.location)
        self._bind_course_module(self.lc_block)
        self.lc_block.xmodule_runtime.publish = self.publisher

    def _install_block_with_descendants(self):
        """
        Replace the blocks in the library with a block that has descendants,
        and return the resulting blocks.
        """
        with self.store.bulk_operations(self.library.location.library_key):
            self.library.children = []
            main_vertical = self.make_block("vertical", self.library)
            inner_vertical = self.make_block("vertical", main_vertical)
            html_block = self.make_block("html", inner_vertical)
            problem_block = self.make_block("problem", inner_vertical)
            self.lc_block.refresh_children()
        return main_vertical, inner_vertical, html_block, problem_block

    def _refresh_lc_block(self):
        """
        Reload lc_block and set it up for a student.
        """
        self.lc_block = self.store.get_item(self.lc_block.location)
        self._bind_course_module(self.lc_block)
        self.lc_block.xmodule_runtime.publish = self.publisher

    def _assert_event_was_published(self, event_type):
        """
        Check that a LibraryContentModule analytics event was published by self.lc_block.
        """
        self.assertTrue(self.publisher.called)
        self.assertTrue(len(self.publisher.call_args[0]), 3)
        _, event_name, event_data = self.publisher.call_args[0]
        self.assertEqual(event_name, "edx.librarycontentblock.content.{}".format(event_type))
        self.assertEqual(event_data["location"], unicode(self.lc_block.location))
        return event_data

    def _assert_assigned_descendants(self, inner_vertical, html_block, problem_block):
        """
        Check that "assigned" event data is correct for block with descendants.
        """
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
            self.assertEqual(len(block_list), 1)  # main_vertical is the only root block added, and is the only result.
            self.assertEqual(block_list[0]["usage_key"], unicode(course_usage_main_vertical))

            # Check that "descendants" is a flat, unordered list of all of main_vertical's descendants:
            descendants_expected = (
                (inner_vertical.location, course_usage_inner_vertical),
                (html_block.location, course_usage_html),
                (problem_block.location, course_usage_problem),
            )
            descendant_data_expected = {}
            for lib_key, course_usage_key in descendants_expected:
                descendant_data_expected[unicode(course_usage_key)] = {
                    "usage_key": unicode(course_usage_key),
                    "original_usage_key": unicode(lib_key),
                    "original_usage_version": unicode(self.store.get_block_original_usage(course_usage_key)[1]),
                }
            self.assertEqual(len(block_list[0]["descendants"]), len(descendant_data_expected))
            for descendant in block_list[0]["descendants"]:
                self.assertEqual(descendant, descendant_data_expected.get(descendant["usage_key"]))

    def test_assigned_event(self):
        """
        Test the "assigned" event emitted when a student is assigned specific blocks.
        """
        # In the beginning was the lc_block and it assigned one child to the student:
        child = self.lc_block.get_child_descriptors()[0]
        child_lib_location, child_lib_version = self.store.get_block_original_usage(child.location)
        self.assertIsInstance(child_lib_version, ObjectId)
        event_data = self._assert_event_was_published("assigned")
        block_info = {
            "usage_key": unicode(child.location),
            "original_usage_key": unicode(child_lib_location),
            "original_usage_version": unicode(child_lib_version),
            "descendants": [],
        }
        self.assertEqual(event_data, {
            "location": unicode(self.lc_block.location),
            "added": [block_info],
            "result": [block_info],
            "previous_count": 0,
            "max_count": 1,
        })
        self.publisher.reset_mock()

        # Now increase max_count so that one more child will be added:
        self.lc_block.max_count = 2
        # Clear the cache (only needed because we skip saving/re-loading the block) pylint: disable=protected-access
        del self.lc_block._xmodule._selected_set
        children = self.lc_block.get_child_descriptors()
        self.assertEqual(len(children), 2)
        child, new_child = children if children[0].location == child.location else reversed(children)
        event_data = self._assert_event_was_published("assigned")
        self.assertEqual(event_data["added"][0]["usage_key"], unicode(new_child.location))
        self.assertEqual(len(event_data["result"]), 2)
        self.assertEqual(event_data["previous_count"], 1)
        self.assertEqual(event_data["max_count"], 2)

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
        dummy, inner_vertical, html_block, problem_block = self._install_block_with_descendants()

        # Reload lc_block and set it up for a student:
        self._refresh_lc_block()

        # Check "assigned" event data:
        self._assert_assigned_descendants(inner_vertical, html_block, problem_block)

    def test_removed_overlimit(self):
        """
        Test the "removed" event emitted when we un-assign blocks previously assigned to a student.
        We go from one blocks assigned to none because max_count has been decreased.
        """
        # Decrease max_count to 1, causing the block to be overlimit:
        self.lc_block.get_child_descriptors()  # This line is needed in the test environment or the change has no effect
        self.publisher.reset_mock()  # Clear the "assigned" event that was just published.
        self.lc_block.max_count = 0
        # Clear the cache (only needed because we skip saving/re-loading the block) pylint: disable=protected-access
        del self.lc_block._xmodule._selected_set

        # Check that the event says that one block was removed, leaving no blocks left:
        children = self.lc_block.get_child_descriptors()
        self.assertEqual(len(children), 0)
        event_data = self._assert_event_was_published("removed")
        self.assertEqual(len(event_data["removed"]), 1)
        self.assertEqual(event_data["result"], [])
        self.assertEqual(event_data["reason"], "overlimit")

    def test_removed_invalid(self):
        """
        Test the "removed" event emitted when we un-assign blocks previously assigned to a student.
        We go from two blocks assigned, to one because the others have been deleted from the library.
        """
        # Start by assigning two blocks to the student:
        self.lc_block.get_child_descriptors()  # This line is needed in the test environment or the change has no effect
        self.lc_block.max_count = 2
        # Clear the cache (only needed because we skip saving/re-loading the block) pylint: disable=protected-access
        del self.lc_block._xmodule._selected_set
        initial_blocks_assigned = self.lc_block.get_child_descriptors()
        self.assertEqual(len(initial_blocks_assigned), 2)
        self.publisher.reset_mock()  # Clear the "assigned" event that was just published.
        # Now make sure that one of the assigned blocks will have to be un-assigned.
        # To cause an "invalid" event, we delete all blocks from the content library
        # except for one of the two already assigned to the student:
        keep_block_key = initial_blocks_assigned[0].location
        keep_block_lib_usage_key, keep_block_lib_version = self.store.get_block_original_usage(keep_block_key)
        self.assertIsNotNone(keep_block_lib_usage_key)
        deleted_block_key = initial_blocks_assigned[1].location
        self.library.children = [keep_block_lib_usage_key]
        self.store.update_item(self.library, self.user_id)
        self.lc_block.refresh_children()
        # Clear the cache (only needed because we skip saving/re-loading the block) pylint: disable=protected-access
        del self.lc_block._xmodule._selected_set

        # Check that the event says that one block was removed, leaving one block left:
        children = self.lc_block.get_child_descriptors()
        self.assertEqual(len(children), 1)
        event_data = self._assert_event_was_published("removed")
        self.assertEqual(event_data["removed"], [{
            "usage_key": unicode(deleted_block_key),
            "original_usage_key": None,  # Note: original_usage_key info is sadly unavailable because the block has been
                                         # deleted so that info can no longer be retrieved
            "original_usage_version": None,
            "descendants": [],
        }])
        self.assertEqual(event_data["result"], [{
            "usage_key": unicode(keep_block_key),
            "original_usage_key": unicode(keep_block_lib_usage_key),
            "original_usage_version": unicode(keep_block_lib_version),
            "descendants": [],
        }])
        self.assertEqual(event_data["reason"], "invalid")


class AdaptiveLibraryContentAnalyticsMixin(LibraryContentAnalyticsMixin):
    """
    Mixin for testing analytics features of adaptive library content modules
    """
    @property
    def pending_reviews(self):
        """
        Return list of pending reviews that consists of relevant and irrelevant reviews.

        A review is relevant to the block under test if it references the parent unit of the block,
        as well as one of the children of the block.
        """
        parent_unit_id = self.vertical.scope_ids.usage_id.block_id
        children = self.lc_block.children
        relevant_reviews = [
            {
                'knowledge_node_uid': parent_unit_id,
                'review_question_uid': child.block_id,

            } for child in children
        ]
        irrelevant_reviews = [
            {
                'knowledge_node_uid': 'knowledge-node-{n}'.format(n=n),
                'review_question_uid': 'review-question-{n}'.format(n=n),
            } for n in range(5)
        ]
        pending_reviews = relevant_reviews + irrelevant_reviews
        return pending_reviews

    def _assert_event_not_published(self):
        """
        Check that *no* AdaptiveLibraryContentModule analytics event was published by self.lc_block.
        """
        self.publisher.assert_not_called()

    def test_assigned_event(self):
        """
        Test the "assigned" event emitted when a student is assigned specific blocks.
        """
        with patch(
            'xmodule.library_content_module.AdaptiveLearningAPIClient.get_pending_reviews'
        ) as patched_get_pending_reviews:
            # In the beginning was the lc_block and it assigned one child to the student:
            patched_get_pending_reviews.return_value = self.pending_reviews[:1]
            child = self.lc_block.get_child_descriptors()[0]
            child_lib_location, child_lib_version = self.store.get_block_original_usage(child.location)
            self.assertIsInstance(child_lib_version, ObjectId)
            event_data = self._assert_event_was_published("assigned")
            block_info = {
                "usage_key": unicode(child.location),
                "original_usage_key": unicode(child_lib_location),
                "original_usage_version": unicode(child_lib_version),
                "descendants": [],
            }
            self.assertEqual(event_data, {
                "location": unicode(self.lc_block.location),
                "added": [block_info],
                "result": [block_info],
                "previous_count": 0,
                "max_count": 1,
            })
            self.publisher.reset_mock()

            # Now increase the number of pending reviews so that one more child will be added:
            patched_get_pending_reviews.return_value = self.pending_reviews[:2]

            # Clear data
            del self.lc_block._xmodule._selected_set  # pylint: disable=protected-access

            # Check children
            children = self.lc_block.get_child_descriptors()
            self.assertEqual(len(children), 2)
            child, new_child = children if children[0].location == child.location else reversed(children)

            # Check event data
            event_data = self._assert_event_was_published("assigned")
            self.assertEqual(event_data["added"][0]["usage_key"], unicode(new_child.location))
            self.assertEqual(len(event_data["result"]), 2)
            self.assertEqual(event_data["previous_count"], 1)

    def test_assigned_event_no_pending_reviews(self):
        """
        Test that no "assigned" event is emitted if student is not assigned any blocks.
        """
        with patch(
            'xmodule.library_content_module.AdaptiveLearningAPIClient.get_pending_reviews'
        ) as patched_get_pending_reviews:
            # In the beginning was the lc_block and it assigned zero children to the student:
            patched_get_pending_reviews.return_value = []
            children = self.lc_block.get_child_descriptors()
            self.assertEqual(len(children), 0)
            self._assert_event_not_published()

    def test_assigned_descendants(self):
        """
        Test the "assigned" event emitted includes descendant block information.
        """
        # Replace the blocks in the library with a block that has descendants:
        dummy, inner_vertical, html_block, problem_block = self._install_block_with_descendants()

        # Reload lc_block and set it up for a student:
        self._refresh_lc_block()

        with patch(
            'xmodule.library_content_module.AdaptiveLearningAPIClient.get_pending_reviews'
        ) as patched_get_pending_reviews:
            patched_get_pending_reviews.return_value = self.pending_reviews

            # Check "assigned" event data:
            self._assert_assigned_descendants(inner_vertical, html_block, problem_block)

    def test_removed_overlimit(self):
        """
        Test that block never drops any elements based on value of `max_count` setting.
        """
        children = self.lc_block.children
        with patch(
            'xmodule.library_content_module.AdaptiveLearningAPIClient.get_pending_reviews'
        ) as patched_get_pending_reviews:
            patched_get_pending_reviews.return_value = self.pending_reviews

            # `max_count` less than number of pending reviews (initial value is 1):
            child_descriptors = self.lc_block.get_child_descriptors()
            self.assertEqual(len(child_descriptors), len(children))
            self._assert_event_not_published()

            # Clear data
            del self.lc_block._xmodule._selected_set  # pylint: disable=protected-access

            # `max_count` equal to number of pending reviews:
            self.lc_block.max_count = 4
            child_descriptors = self.lc_block.get_child_descriptors()
            self.assertEqual(len(child_descriptors), len(children))
            self._assert_event_not_published()

            # Clear data
            del self.lc_block._xmodule._selected_set   # pylint: disable=protected-access

            # `max_count` greater than number of pending reviews:
            self.lc_block.max_count = 8
            child_descriptors = self.lc_block.get_child_descriptors()
            self.assertEqual(len(child_descriptors), len(children))
            self._assert_event_not_published()

    def test_removed_invalid(self):
        """
        Test the "removed" event emitted when we un-assign blocks previously assigned to a student.
        We go from four blocks assigned, to one because the others have been deleted from the library.
        """
        children = self.lc_block.children
        with patch(
            'xmodule.library_content_module.AdaptiveLearningAPIClient.get_pending_reviews'
        ) as patched_get_pending_reviews:
            patched_get_pending_reviews.return_value = self.pending_reviews

            # Start by assigning four child blocks to the student:
            initial_blocks_assigned = self.lc_block.get_child_descriptors()
            self.assertEqual(len(initial_blocks_assigned), len(children))

            # Now make sure that all but one of the assigned blocks will have to be un-assigned.
            # To cause an "invalid" event, we delete all blocks from the content library
            # except for one of the four already assigned to the student:
            keep_block_key = initial_blocks_assigned[0].location
            keep_block_lib_usage_key, keep_block_lib_version = self.store.get_block_original_usage(keep_block_key)
            self.assertIsNotNone(keep_block_lib_usage_key)
            deleted_block_keys = [block.location for block in initial_blocks_assigned[1:]]
            self.library.children = [keep_block_lib_usage_key]
            self.store.update_item(self.library, self.user_id)
            self.lc_block.refresh_children()

            # Clear data
            del self.lc_block._xmodule._selected_set  # pylint: disable=protected-access

            # Update selected blocks
            child_descriptors = self.lc_block.get_child_descriptors()

            # Check that the event says that three blocks were removed, leaving one block:
            event_data = self._assert_event_was_published("removed")
            self.assertEqual(len(child_descriptors), 1)
            expected_deleted_block_keys = [{
                "usage_key": unicode(deleted_block_key),
                # Note: original_usage_key info is sadly unavailable
                # because the block has been deleted so that info can no longer be retrieved
                "original_usage_key": None,
                "original_usage_version": None,
                "descendants": [],
            } for deleted_block_key in deleted_block_keys]
            self.assertEqual(len(event_data["removed"]), len(expected_deleted_block_keys))
            for expected_deleted_block_key in expected_deleted_block_keys:
                self.assertIn(expected_deleted_block_key, event_data["removed"])

            self.assertEqual(event_data["result"], [{
                "usage_key": unicode(keep_block_key),
                "original_usage_key": unicode(keep_block_lib_usage_key),
                "original_usage_version": unicode(keep_block_lib_version),
                "descendants": [],
            }])
            self.assertEqual(event_data["reason"], "invalid")


class TestLibraryContentAnalytics(LibraryContentAnalyticsMixin, LibraryContentTest):
    """
    Test analytics features of LibraryContentModule
    """
    pass


class TestAdaptiveLibraryContentAnalytics(AdaptiveLibraryContentAnalyticsMixin, AdaptiveLibraryContentTest):
    """
    Test analytics features of AdaptiveLibraryContentModule
    """
    pass
