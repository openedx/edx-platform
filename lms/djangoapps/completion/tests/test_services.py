"""
Tests of completion xblock runtime services
"""
import ddt
from django.test import TestCase
from opaque_keys.edx.keys import CourseKey, UsageKey
from student.tests.factories import UserFactory

from ..models import BlockCompletion
from ..services import CompletionService
from ..test_utils import CompletionWaffleTestMixin


@ddt.ddt
class CompletionServiceTestCase(CompletionWaffleTestMixin, TestCase):
    """
    Test the data returned by the CompletionService.
    """

    def setUp(self):
        super(CompletionServiceTestCase, self).setUp()
        self.override_waffle_switch(True)
        self.user = UserFactory.create()
        self.other_user = UserFactory.create()
        self.course_key = CourseKey.from_string("edX/MOOC101/2049_T2")
        self.other_course_key = CourseKey.from_string("course-v1:ReedX+Hum110+1904")
        self.block_keys = [UsageKey.from_string("i4x://edX/MOOC101/video/{}".format(number)) for number in xrange(5)]

        self.completion_service = CompletionService(self.user, self.course_key)

        # Proper completions for the given runtime
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
                self.block_keys[4]: 0.0,
            },
        )

    @ddt.data(True, False)
    def test_enabled_honors_waffle_switch(self, enabled):
        self.override_waffle_switch(enabled)
        self.assertEqual(self.completion_service.completion_tracking_enabled(), enabled)
