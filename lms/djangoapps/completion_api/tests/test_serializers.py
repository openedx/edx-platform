"""
Test serialization of completion data.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from operator import itemgetter

import ddt
from django.test import TestCase
from django.test.utils import override_settings

from opaque_keys.edx.keys import CourseKey, UsageKey
from progress import models

from edx_solutions_api_integration.test_utils import SignalDisconnectTestMixin
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import ToyCourseFactory
from ..serializers import course_completion_serializer_factory
from ..models import CourseCompletionFacade, _Stats


class MockCourseCompletion(CourseCompletionFacade):
    """
    Provide CourseCompletion info without hitting the modulestore.
    """
    def __init__(self, progress):
        super(MockCourseCompletion, self).__init__(progress)
        self._possible = 19

    @property
    def stats(self):
        return _Stats(earned=16, possible=19)

    @property
    def possible(self):
        """
        Make up a number of possible blocks.  This prevents completable_blocks
        from being called, which prevents hitting the modulestore.
        """
        return self._possible

    @possible.setter
    def possible(self, value):  # pylint: disable=arguments-differ
        self._possible = value

    @property
    def sequential(self):
        return [
            {'course_key': self.course_key, 'block_key': 'block1', 'earned': 6.0, 'possible': 7.0, 'ratio': 6 / 7},
            {'course_key': self.course_key, 'block_key': 'block2', 'earned': 10.0, 'possible': 12.0, 'ratio': 5 / 6},
        ]


@ddt.ddt
class CourseCompletionSerializerTestCase(TestCase):
    """
    Test that the CourseCompletionSerializer returns appropriate results.
    """

    def setUp(self):
        super(CourseCompletionSerializerTestCase, self).setUp()
        self.test_user = UserFactory.create()

    @ddt.data(
        [course_completion_serializer_factory([]), {}],
        [
            course_completion_serializer_factory(['sequential']),
            {
                'sequential': [
                    {
                        'course_key': 'course-v1:abc+def+ghi',
                        'block_key': 'block1',
                        'completion': {'earned': 6.0, 'possible': 7.0, 'ratio': 6 / 7},
                    },
                    {
                        'course_key': 'course-v1:abc+def+ghi',
                        'block_key': 'block2',
                        'completion': {'earned': 10.0, 'possible': 12.0, 'ratio': 5 / 6},
                    },
                ]
            }
        ]
    )
    @ddt.unpack
    def test_serialize_student_progress_object(self, serializer_cls, extra_body):
        progress = models.StudentProgress.objects.create(
            user=self.test_user,
            course_id=CourseKey.from_string('course-v1:abc+def+ghi'),
            completions=16,
        )
        completion = MockCourseCompletion(progress)
        serial = serializer_cls(completion)
        expected = {
            'course_key': 'course-v1:abc+def+ghi',
            'completion': {
                'earned': 16.0,
                'possible': 19.0,
                'ratio': 16 / 19,
            },
        }
        expected.update(extra_body)
        self.assertEqual(
            serial.data,
            expected,
        )

    def test_zero_possible(self):
        progress = models.StudentProgress.objects.create(
            user=self.test_user,
            course_id=CourseKey.from_string('course-v1:abc+def+ghi'),
            completions=0,
        )
        completion = MockCourseCompletion(progress)
        completion.possible = 0
        serial = course_completion_serializer_factory([])(completion)
        self.assertEqual(
            serial.data['completion'],
            {
                'earned': 16.0,
                'possible': 0.0,
                'ratio': 1.0,
            },
        )


@ddt.ddt
@override_settings(STUDENT_GRADEBOOK=True)
class ToyCourseCompletionTestCase(SignalDisconnectTestMixin, SharedModuleStoreTestCase):
    """
    Test that the CourseCompletionFacade handles modulestore data appropriately,
    and that it interacts properly with the serializer.
    """

    @classmethod
    def setUpClass(cls):
        super(ToyCourseCompletionTestCase, cls).setUpClass()
        cls.course = ToyCourseFactory.create()

    def setUp(self):
        super(ToyCourseCompletionTestCase, self).setUp()
        self.test_user = UserFactory.create()
        CourseEnrollment.enroll(self.test_user, self.course.id)

    def test_no_completions(self):
        progress = models.StudentProgress.objects.create(
            user=self.test_user,
            course_id=self.course.id,
            completions=0,
        )
        completion = CourseCompletionFacade(progress)
        self.assertEqual(completion.earned, 0.0)
        self.assertEqual(completion.possible, 12.0)
        serial = course_completion_serializer_factory([])(completion)
        self.assertEqual(
            serial.data,
            {
                'course_key': 'edX/toy/2012_Fall',
                'completion': {
                    'earned': 0.0,
                    'possible': 12.0,
                    'ratio': 0.0,
                }
            }
        )

    def test_with_completions(self):
        for block_id in ('sample_video', 'separate_file_video', 'video_with_end_time'):
            usage_key_str = 'i4x://edX/toy/video/{}'.format(block_id)
            models.CourseModuleCompletion.objects.create(
                user=self.test_user,
                course_id=self.course.id,
                content_id=UsageKey.from_string(usage_key_str).map_into_course(self.course.id),
            )
        # Now, check the result:
        progress = models.StudentProgress.objects.get(user=self.test_user, course_id=self.course.id)
        completion = CourseCompletionFacade(progress)
        self.assertEqual(completion.earned, 3)
        self.assertEqual(completion.possible, 12)
        # A sequential exists, but isn't included in the output
        self.assertEqual(len(completion.sequential), 1)
        serial = course_completion_serializer_factory([])(completion)
        self.assertEqual(
            serial.data,
            {
                'course_key': 'edX/toy/2012_Fall',
                'completion': {
                    'earned': 3.0,
                    'possible': 12.0,
                    'ratio': 3 / 12,
                }
            }
        )

    def test_with_sequentials(self):
        block_key = UsageKey.from_string("i4x://edX/toy/video/sample_video")
        block_key = block_key.map_into_course(self.course.id)
        models.CourseModuleCompletion.objects.create(
            user=self.test_user,
            course_id=self.course.id,
            content_id=block_key,
        )
        progress = models.StudentProgress.objects.get(user=self.test_user, course_id=self.course.id)
        completion = CourseCompletionFacade(progress)
        serial = course_completion_serializer_factory(['sequential'])(completion)
        self.assertEqual(
            serial.data,
            {
                'course_key': 'edX/toy/2012_Fall',
                'completion': {
                    'earned': 1.0,
                    'possible': 12.0,
                    'ratio': 1 / 12,
                },
                'sequential': [
                    {
                        'course_key': u'edX/toy/2012_Fall',
                        'block_key': u'i4x://edX/toy/sequential/vertical_sequential',
                        'completion': {'earned': 1.0, 'possible': 5.0, 'ratio': 0.20},
                    },
                ]
            }
        )

    @ddt.data(0, 1, 2, 3, 4, 5)
    def test_with_mean(self, extra_users):
        # Base mean should be 1/12, but we're using legacy calculations.
        base_mean = 0.25
        mean = base_mean / (1 + extra_users)
        for _ in xrange(extra_users):
            user = UserFactory.create()
            CourseEnrollment.enroll(user=user, course_key=self.course.id)
        block_key = UsageKey.from_string("i4x://edX/toy/video/sample_video")
        block_key = block_key.map_into_course(self.course.id)
        models.CourseModuleCompletion.objects.create(
            user=self.test_user,
            course_id=self.course.id,
            content_id=block_key,
        )
        progress = models.StudentProgress.objects.get(user=self.test_user, course_id=self.course.id)
        completion = CourseCompletionFacade(progress)
        # Float rounding errors get introduced, so we use assertAlmostEqual.
        self.assertAlmostEqual(completion.mean, mean)
        serial = course_completion_serializer_factory({'mean'})(completion, {'mean'})
        self.assertEqual(
            serial.data,
            {
                'course_key': 'edX/toy/2012_Fall',
                'completion': {
                    'earned': 1.0,
                    'possible': 12.0,
                    'ratio': 1 / 12,
                },
                'mean': completion.mean,
            }
        )

    def test_with_all_requested_fields(self):
        # Mean should be 1/12, but we're using legacy calculations.
        mean = 0.25
        block_key = UsageKey.from_string("i4x://edX/toy/video/sample_video")
        block_key = block_key.map_into_course(self.course.id)
        models.CourseModuleCompletion.objects.create(
            user=self.test_user,
            course_id=self.course.id,
            content_id=block_key,
        )
        progress = models.StudentProgress.objects.get(user=self.test_user, course_id=self.course.id)
        completion = CourseCompletionFacade(progress)
        serializer_cls = course_completion_serializer_factory({'chapter', 'mean', 'sequential', 'vertical'})
        serial = serializer_cls(completion, {'chapter', 'mean', 'sequential', 'vertical'})
        data = serial.data
        # Modulestore returns the blocks in non-deterministic order.
        # Don't require a particular ordering here.
        chapters = sorted(data.pop('chapter'), key=itemgetter('block_key'))
        self.assertEqual(
            chapters,
            [
                {
                    'course_key': u'edX/toy/2012_Fall',
                    'block_key': u'i4x://edX/toy/chapter/Overview',
                    'completion': {'earned': 0.0, 'possible': 4.0, 'ratio': 0.0},
                },
                {
                    'course_key': u'edX/toy/2012_Fall',
                    'block_key': u'i4x://edX/toy/chapter/handout_container',
                    'completion': {'earned': 0.0, 'possible': 1.0, 'ratio': 0.0},
                },
                {
                    'course_key': u'edX/toy/2012_Fall',
                    'block_key': u'i4x://edX/toy/chapter/poll_test',
                    'completion': {'earned': 0.0, 'possible': 1.0, 'ratio': 0.0},
                },
                {
                    'course_key': u'edX/toy/2012_Fall',
                    'block_key': u'i4x://edX/toy/chapter/secret:magic',
                    'completion': {'earned': 0.0, 'possible': 1.0, 'ratio': 0.0},
                },
                {
                    'course_key': u'edX/toy/2012_Fall',
                    'block_key': u'i4x://edX/toy/chapter/vertical_container',
                    'completion': {'earned': 1.0, 'possible': 5.0, 'ratio': 0.2},
                },
            ]
        )
        self.assertEqual(
            data,
            {
                u'course_key': u'edX/toy/2012_Fall',
                u'completion': {'earned': 1.0, 'possible': 12.0, 'ratio': 1 / 12},
                u'sequential': [
                    {
                        'course_key': u'edX/toy/2012_Fall',
                        'block_key': u'i4x://edX/toy/sequential/vertical_sequential',
                        'completion': {'earned': 1.0, 'possible': 5.0, 'ratio': 0.2},
                    },
                ],
                u'vertical': [
                    {
                        'course_key': u'edX/toy/2012_Fall',
                        'block_key': u'i4x://edX/toy/vertical/vertical_test',
                        'completion': {'earned': 1.0, 'possible': 4.0, 'ratio': 0.25}
                    }
                ],
                u'mean': mean,

            }
        )
