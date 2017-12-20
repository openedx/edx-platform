"""
Test serialization of completion data.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import ddt
from django.test import TestCase
from opaque_keys.edx.keys import CourseKey

from student.tests.factories import UserFactory
from .. import models
from ..serializers import course_completion_serializer_factory, CourseAggregationAdapter
from ..test_utils import CompletionWaffleTestMixin


class CourseAggregationAdapterTestCase(CompletionWaffleTestMixin, TestCase):
    """
    Test the behavior of the CourseAggregationAdapter
    """
    def setUp(self):
        super(CourseAggregationAdapterTestCase, self).setUp()
        self.override_waffle_switch(True)
        self.override_aggregation_switch(True)
        self.test_user = UserFactory.create()
        self.course_key = CourseKey.from_string("course-v1:z+b+c")

    def test_simple_aggregation_structure(self):
        course_completion, _ = models.AggregateCompletion.objects.submit_completion(
            user=self.test_user,
            course_key=self.course_key,
            block_key=self.course_key.make_usage_key(block_type='course', block_id='crs'),
            aggregation_name='course',
            earned=4.2,
            possible=9.6,
        )
        chapter_completion, _ = models.AggregateCompletion.objects.submit_completion(
            user=self.test_user,
            course_key=self.course_key,
            block_key=self.course_key.make_usage_key(block_type='chapter', block_id='chap1'),
            aggregation_name='chapter',
            earned=1.8,
            possible=3.4,
        )
        agstruct = CourseAggregationAdapter(
            user=self.test_user,
            course_key=self.course_key,
        )
        agstruct.add_aggregate_completion(course_completion)
        agstruct.update_aggregate_completions([chapter_completion])

        self.assertEqual(agstruct.course, course_completion)
        self.assertEqual(agstruct.chapter, [chapter_completion])


@ddt.ddt
class CourseCompletionSerializerTestCase(CompletionWaffleTestMixin, TestCase):
    """
    Test that the CourseCompletionSerializer returns appropriate results.
    """

    def setUp(self):
        super(CourseCompletionSerializerTestCase, self).setUp()
        self.override_waffle_switch(True)
        self.override_aggregation_switch(True)
        self.test_user = UserFactory.create()

    @ddt.data(
        [course_completion_serializer_factory([]), {}],
        [
            course_completion_serializer_factory(['sequential']),
            {
                'sequential': [
                    {
                        'course_key': 'course-v1:abc+def+ghi',
                        'block_key': 'block-v1:abc+def+ghi+type@sequential+block@seq1',
                        'completion': {'earned': 6.0, 'possible': 7.0, 'percent': 6 / 7},
                    },
                    {
                        'course_key': 'course-v1:abc+def+ghi',
                        'block_key': 'block-v1:abc+def+ghi+type@sequential+block@seq2',
                        'completion': {'earned': 10.0, 'possible': 12.0, 'percent': 5 / 6},
                    },
                ]
            }
        ]
    )
    @ddt.unpack
    def test_serialize_student_progress_object(self, serializer_cls, extra_body):
        course_key = CourseKey.from_string('course-v1:abc+def+ghi')
        completions = [
            models.AggregateCompletion.objects.submit_completion(
                user=self.test_user,
                course_key=course_key,
                aggregation_name='course',
                block_key=course_key.make_usage_key(block_type='course', block_id='crs'),
                earned=16.0,
                possible=19.0,
            )[0],
            models.AggregateCompletion.objects.submit_completion(
                user=self.test_user,
                course_key=course_key,
                aggregation_name='sequential',
                block_key=course_key.make_usage_key(block_type='sequential', block_id='seq1'),
                earned=6.0,
                possible=7.0,
            )[0],
            models.AggregateCompletion.objects.submit_completion(
                user=self.test_user,
                course_key=course_key,
                aggregation_name='sequential',
                block_key=course_key.make_usage_key(block_type='sequential', block_id='seq2'),
                earned=10.0,
                possible=12.0,
            )[0],
        ]
        completion = CourseAggregationAdapter(
            user=self.test_user,
            course_key=course_key,
            queryset=completions,
        )
        serial = serializer_cls(completion)
        expected = {
            'course_key': 'course-v1:abc+def+ghi',
            'completion': {
                'earned': 16.0,
                'possible': 19.0,
                'percent': 16 / 19,
            },
        }
        expected.update(extra_body)
        self.assertEqual(
            serial.data,
            expected,
        )

    def test_zero_possible(self):
        course_key = CourseKey.from_string('course-v1:abc+def+ghi')
        completion, _ = models.AggregateCompletion.objects.submit_completion(
            user=self.test_user,
            course_key=course_key,
            block_key=course_key.make_usage_key(block_type='course', block_id='course'),
            aggregation_name='course',
            earned=0.0,
            possible=0.0,
        )

        serial = course_completion_serializer_factory([])(CourseAggregationAdapter(
            user=self.test_user,
            course_key=course_key,
            queryset=[completion]
        ))
        self.assertEqual(
            serial.data['completion'],
            {
                'earned': 0.0,
                'possible': 0.0,
                'percent': 1.0,
            },
        )
