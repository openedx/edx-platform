"""
Tests for generic sequence-featching API tests.

Use the learning_sequences outlines API to create test data.
Do not import/create/mock learning_sequences models directly.
"""
from datetime import datetime, timezone

from django.test import TestCase
from opaque_keys.edx.keys import CourseKey

from ...api import replace_course_outline
from ...data import (
    hash_usage_key,
    CourseLearningSequenceData,
    CourseSectionData,
    CourseOutlineData,
    CourseVisibility,
    LearningSequenceData,
    VisibilityData,
)
from ..sequences import get_learning_sequence, get_learning_sequence_by_hash
from .test_data import generate_sections


class GetLearningSequenceTestCase(TestCase):
    """
    Test get_learning_sequence and get_learning_sequence_by_hash.
    """

    common_course_outline_fields = dict(
        published_at=datetime(2021, 8, 12, tzinfo=timezone.utc),
        entrance_exam_id=None,
        days_early_for_beta=None,
        self_paced=False,
        course_visibility=CourseVisibility.PRIVATE,
    )

    @classmethod
    def setUpTestData(cls):
        """
        Set up test data, to be reusable across all tests in this class.
        """
        super().setUpTestData()
        cls.course_key = CourseKey.from_string("course-v1:Open-edX+Learn+GetSeq")
        cls.course_outline = CourseOutlineData(
            course_key=cls.course_key,
            title="Get Learning Sequences Test Course!",
            published_version="5ebece4b69cc593d82fe2021",
            sections=generate_sections(cls.course_key, [0, 2, 1]),
            **cls.common_course_outline_fields,
        )
        replace_course_outline(cls.course_outline)
        cls.sequence_key = cls.course_outline.sections[1].sequences[1].usage_key
        cls.sequence_key_hash = hash_usage_key(cls.sequence_key)
        cls.fake_sequence_key = cls.course_key.make_usage_key('sequential', 'fake_sequence')
        cls.fake_sequence_key_hash = hash_usage_key(cls.fake_sequence_key)

    def test_get_learning_sequence_not_found(self):
        with self.assertRaises(LearningSequenceData.DoesNotExist):
            get_learning_sequence(self.fake_sequence_key)

    def test_get_learning_sequence_by_hash_not_found(self):
        with self.assertRaises(LearningSequenceData.DoesNotExist):
            get_learning_sequence_by_hash(self.fake_sequence_key_hash)

    def test_get_learning_sequence(self):
        sequence = get_learning_sequence(self.sequence_key)
        assert isinstance(sequence, LearningSequenceData)
        assert sequence.usage_key == self.sequence_key
        assert sequence.usage_key_hash == self.sequence_key_hash

    def test_get_learning_sequence_by_hash(self):
        sequence = get_learning_sequence_by_hash(self.sequence_key_hash)
        assert isinstance(sequence, LearningSequenceData)
        assert sequence.usage_key == self.sequence_key
        assert sequence.usage_key_hash == self.sequence_key_hash

    def test_get_learning_sequence_hash_collision(self):
        normal_visibility = VisibilityData(
            hide_from_toc=False,
            visible_to_staff_only=False
        )
        course_key_1 = CourseKey.from_string("course-v1:Open-edX+Learn+Collide1")
        outline_1 = CourseOutlineData(
            course_key=course_key_1,
            title="Learning Sequences - Collision Course 1",
            published_version="5ebece4b79cc593d82fe2021",
            sections=[
                CourseSectionData(
                    usage_key=course_key_1.make_usage_key('chapter', 'ch_a'),
                    title="Chapter A",
                    visibility=normal_visibility,
                    sequences=[
                        CourseLearningSequenceData(
                            usage_key=course_key_1.make_usage_key('sequential', 'seq_a'),
                            usage_key_hash="2COLLIDE",
                            title="Seq A",
                            visibility=normal_visibility,
                        )
                    ]
                )
            ],
            **self.common_course_outline_fields,
        )
        course_key_2 = CourseKey.from_string("course-v1:Open-edX+Learn+Collide2")
        outline_2 = CourseOutlineData(
            course_key=course_key_2,
            title="Learning Sequences - Collision Course 2",
            published_version="5ebece4b89cc593d82fe2021",
            sections=[
                CourseSectionData(
                    usage_key=course_key_2.make_usage_key('chapter', 'ch_a'),
                    title="Chapter A",
                    visibility=normal_visibility,
                    sequences=[
                        CourseLearningSequenceData(
                            usage_key=course_key_2.make_usage_key('sequential', 'seq_a'),
                            usage_key_hash="2COLLIDE",
                            title="Seq A",
                            visibility=normal_visibility,
                        )
                    ]
                )
            ],
            **self.common_course_outline_fields,
        )
        replace_course_outline(outline_1)
        replace_course_outline(outline_2)
        with self.assertRaises(Exception) as exc:
            get_learning_sequence_by_hash("2COLLIDE")
        message = str(exc.exception)
        assert "Two or more sequences" in message
        assert str(outline_1.sections[0].sequences[0].usage_key) in message
        assert str(outline_2.sections[0].sequences[0].usage_key) in message
