"""
Tests of completion xblock runtime services
"""


import ddt
from completion.models import BlockCompletion
from completion.services import CompletionService
from completion.test_utils import CompletionWaffleTestMixin
from opaque_keys.edx.keys import CourseKey
from six.moves import range

from openedx.core.djangolib.testing.utils import skip_unless_lms
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.library_tools import LibraryToolsService
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase, TEST_DATA_SPLIT_MODULESTORE
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, LibraryFactory
from xmodule.tests import get_test_system


@ddt.ddt
@skip_unless_lms
class CompletionServiceTestCase(CompletionWaffleTestMixin, SharedModuleStoreTestCase):
    """
    Test the data returned by the CompletionService.
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @classmethod
    def setUpClass(cls):
        super(CompletionServiceTestCase, cls).setUpClass()
        cls.course = CourseFactory.create()
        with cls.store.bulk_operations(cls.course.id):
            cls.chapter = ItemFactory.create(
                parent=cls.course,
                category="chapter",
                publish_item=False,
            )
            cls.sequence = ItemFactory.create(
                parent=cls.chapter,
                category='sequential',
                publish_item=False,
            )
            cls.vertical = ItemFactory.create(
                parent=cls.sequence,
                category='vertical',
                publish_item=False,
            )
            cls.html = ItemFactory.create(
                parent=cls.vertical,
                category='html',
                publish_item=False,
            )
            cls.problem = ItemFactory.create(
                parent=cls.vertical,
                category="problem",
                publish_item=False,
            )
            cls.problem2 = ItemFactory.create(
                parent=cls.vertical,
                category="problem",
                publish_item=False,
            )
            cls.problem3 = ItemFactory.create(
                parent=cls.vertical,
                category="problem",
                publish_item=False,
            )
            cls.problem4 = ItemFactory.create(
                parent=cls.vertical,
                category="problem",
                publish_item=False,
            )
            cls.problem5 = ItemFactory.create(
                parent=cls.vertical,
                category="problem",
                publish_item=False,
            )
            cls.store.update_item(cls.course, UserFactory().id)
        cls.problems = [cls.problem, cls.problem2, cls.problem3, cls.problem4, cls.problem5]

    def setUp(self):
        super(CompletionServiceTestCase, self).setUp()
        self.override_waffle_switch(True)
        self.user = UserFactory.create()
        self.other_user = UserFactory.create()
        self.course_key = self.course.id
        self.other_course_key = CourseKey.from_string("course-v1:ReedX+Hum110+1904")
        self.block_keys = [problem.location for problem in self.problems]
        self.completion_service = CompletionService(self.user, self.course_key)

        # Proper completions for the given runtime
        BlockCompletion.objects.submit_completion(
            user=self.user,
            block_key=self.html.location,
            completion=1.0,
        )

        for idx, block_key in enumerate(self.block_keys[0:3]):
            BlockCompletion.objects.submit_completion(
                user=self.user,
                block_key=block_key,
                completion=1.0 - (0.2 * idx),
            )

        # Wrong user
        for idx, block_key in enumerate(self.block_keys[2:]):
            BlockCompletion.objects.submit_completion(
                user=self.other_user,
                block_key=block_key,
                completion=0.9 - (0.2 * idx),
            )

        # Wrong course
        BlockCompletion.objects.submit_completion(
            user=self.user,
            block_key=self.other_course_key.make_usage_key('problem', 'other'),
            completion=0.75,
        )

    def _bind_course_module(self, module):
        """
        Bind a module (part of self.course) so we can access student-specific data.
        """
        module_system = get_test_system(course_id=module.location.course_key)
        module_system.descriptor_runtime = module.runtime._descriptor_system  # pylint: disable=protected-access
        module_system._services['library_tools'] = LibraryToolsService(self.store, self.user.id)  # pylint: disable=protected-access

        def get_module(descriptor):
            """Mocks module_system get_module function"""
            sub_module_system = get_test_system(course_id=module.location.course_key)
            sub_module_system.get_module = get_module
            sub_module_system.descriptor_runtime = descriptor._runtime  # pylint: disable=protected-access
            descriptor.bind_for_student(sub_module_system, self.user.id)
            return descriptor

        module_system.get_module = get_module
        module.xmodule_runtime = module_system

    def test_completion_service(self):
        # Only the completions for the user and course specified for the CompletionService
        # are returned.  Values are returned for all keys provided.
        self.assertEqual(
            self.completion_service.get_completions(self.block_keys),
            {
                self.block_keys[0]: 1.0,
                self.block_keys[1]: 0.8,
                self.block_keys[2]: 0.6,
                self.block_keys[3]: 0.0,
                self.block_keys[4]: 0.0
            },
        )

    @ddt.data(True, False)
    def test_enabled_honors_waffle_switch(self, enabled):
        self.override_waffle_switch(enabled)
        self.assertEqual(self.completion_service.completion_tracking_enabled(), enabled)

    def test_vertical_completion(self):
        self.assertEqual(
            self.completion_service.vertical_is_complete(self.vertical),
            False,
        )

        for block_key in self.block_keys:
            BlockCompletion.objects.submit_completion(
                user=self.user,
                block_key=block_key,
                completion=1.0
            )

        self.assertEqual(
            self.completion_service.vertical_is_complete(self.vertical),
            True,
        )

    def test_vertical_partial_completion(self):
        block_keys_count = len(self.block_keys)
        for i in range(block_keys_count - 1):
            # Mark all the child blocks completed except the last one
            BlockCompletion.objects.submit_completion(
                user=self.user,
                block_key=self.block_keys[i],
                completion=1.0
            )

        self.assertEqual(
            self.completion_service.vertical_is_complete(self.vertical),
            False,
        )

    def test_can_mark_block_complete_on_view(self):

        self.assertEqual(self.completion_service.can_mark_block_complete_on_view(self.course), False)
        self.assertEqual(self.completion_service.can_mark_block_complete_on_view(self.chapter), False)
        self.assertEqual(self.completion_service.can_mark_block_complete_on_view(self.sequence), False)
        self.assertEqual(self.completion_service.can_mark_block_complete_on_view(self.vertical), False)
        self.assertEqual(self.completion_service.can_mark_block_complete_on_view(self.html), True)
        self.assertEqual(self.completion_service.can_mark_block_complete_on_view(self.problem), False)

    def test_vertical_completion_with_library_content(self):
        library = LibraryFactory.create(modulestore=self.store)
        ItemFactory.create(parent=library, category='problem', publish_item=False, user_id=self.user.id)
        ItemFactory.create(parent=library, category='problem', publish_item=False, user_id=self.user.id)
        ItemFactory.create(parent=library, category='problem', publish_item=False, user_id=self.user.id)
        lib_vertical = ItemFactory.create(parent=self.sequence, category='vertical', publish_item=False)
        library_content_block = ItemFactory.create(
            parent=lib_vertical,
            category='library_content',
            max_count=1,
            source_library_id=str(library.location.library_key),
            user_id=self.user.id,
        )
        library_content_block.refresh_children()
        lib_vertical = self.store.get_item(lib_vertical.location)
        self._bind_course_module(lib_vertical)
        # We need to refetch the library_content_block to retrieve the
        # fresh version from the call to get_item for lib_vertical
        library_content_block = [child for child in lib_vertical.get_children()
                                 if child.scope_ids.block_type == 'library_content'][0]

        ## Ensure the library_content_block is properly set up
        # This is needed so we can call get_child_descriptors
        self._bind_course_module(library_content_block)
        # Make sure the runtime knows that the block's children vary per-user:
        self.assertTrue(library_content_block.has_dynamic_children())
        self.assertEqual(len(library_content_block.children), 3)
        # Check how many children each user will see:
        self.assertEqual(len(library_content_block.get_child_descriptors()), 1)

        # No problems are complete yet
        self.assertFalse(self.completion_service.vertical_is_complete(lib_vertical))

        for block_key in self.block_keys:
            BlockCompletion.objects.submit_completion(
                user=self.user,
                block_key=block_key,
                completion=1.0
            )
        # Library content problems aren't complete yet
        self.assertFalse(self.completion_service.vertical_is_complete(lib_vertical))

        for child in library_content_block.get_child_descriptors():
            BlockCompletion.objects.submit_completion(
                user=self.user,
                block_key=child.scope_ids.usage_id,
                completion=1.0
            )
        self.assertTrue(self.completion_service.vertical_is_complete(lib_vertical))

    def test_vertical_completion_with_nested_children(self):
        parent_vertical = ItemFactory(parent=self.sequence, category='vertical')
        extra_vertical = ItemFactory(parent=parent_vertical, category='vertical')
        problem = ItemFactory(parent=extra_vertical, category='problem')
        parent_vertical = self.store.get_item(parent_vertical.location)

        # Nothing is complete
        self.assertFalse(self.completion_service.vertical_is_complete(parent_vertical))

        for block_key in self.block_keys:
            BlockCompletion.objects.submit_completion(
                user=self.user,
                block_key=block_key,
                completion=1.0
            )
        # The nested child isn't complete yet
        self.assertFalse(self.completion_service.vertical_is_complete(parent_vertical))

        BlockCompletion.objects.submit_completion(
            user=self.user,
            block_key=problem.location,
            completion=1.0
        )
        self.assertTrue(self.completion_service.vertical_is_complete(parent_vertical))
