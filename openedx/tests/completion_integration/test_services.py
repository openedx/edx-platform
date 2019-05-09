"""
Tests of completion xblock runtime services
"""
from completion.models import BlockCompletion
from completion.services import CompletionService
from completion.test_utils import CompletionWaffleTestMixin
import ddt
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangolib.testing.utils import skip_unless_lms
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


@ddt.ddt
@skip_unless_lms
class CompletionServiceTestCase(CompletionWaffleTestMixin, SharedModuleStoreTestCase):
    """
    Test the data returned by the CompletionService.
    """
    @classmethod
    def setUpClass(cls):
        super(CompletionServiceTestCase, cls).setUpClass()
        cls.course = CourseFactory.create()
        with cls.store.bulk_operations(cls.course.id):
            cls.chapter = ItemFactory.create(
                parent=cls.course,
                category="chapter",
            )
            cls.sequence = ItemFactory.create(
                parent=cls.chapter,
                category='sequential',
            )
            cls.vertical = ItemFactory.create(
                parent=cls.sequence,
                category='vertical',
            )
            cls.html = ItemFactory.create(
                parent=cls.vertical,
                category='html',
            )
            cls.problem = ItemFactory.create(
                parent=cls.vertical,
                category="problem",
            )
            cls.problem2 = ItemFactory.create(
                parent=cls.vertical,
                category="problem",
            )
            cls.problem3 = ItemFactory.create(
                parent=cls.vertical,
                category="problem",
            )
            cls.problem4 = ItemFactory.create(
                parent=cls.vertical,
                category="problem",
            )
            cls.problem5 = ItemFactory.create(
                parent=cls.vertical,
                category="problem",
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
            course_key=self.course_key,
            block_key=self.html.location,
            completion=1.0,
        )

        for idx, block_key in enumerate(self.block_keys[0:3]):
            BlockCompletion.objects.submit_completion(
                user=self.user,
                course_key=self.course_key,
                block_key=block_key,
                completion=1.0 - (0.2 * idx),
            )

        # Wrong user
        for idx, block_key in enumerate(self.block_keys[2:]):
            BlockCompletion.objects.submit_completion(
                user=self.other_user,
                course_key=self.course_key,
                block_key=block_key,
                completion=0.9 - (0.2 * idx),
            )

        # Wrong course
        BlockCompletion.objects.submit_completion(
            user=self.user,
            course_key=self.other_course_key,
            block_key=self.block_keys[4],
            completion=0.75,
        )

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
                course_key=self.course_key,
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
                course_key=self.course_key,
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
