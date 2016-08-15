"""
Unit tests for grades models.
"""
from base64 import b64encode
from collections import OrderedDict
import ddt
from hashlib import sha256
import json
from mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from opaque_keys.edx.locator import CourseLocator, BlockUsageLocator

from lms.djangoapps.grades.models import BlockRecord, VisibleBlocks, PersistentSubsectionGrade


class GradesModelTestCase(TestCase):
    """
    Base class for common setup of grades model tests.
    """
    def setUp(self):
        super(GradesModelTestCase, self).setUp()
        self.course_key = CourseLocator(
            org='some_org',
            course='some_course',
            run='some_run'
        )
        self.locator_a = BlockUsageLocator(
            course_key=self.course_key,
            block_type='problem',
            block_id='block_id_a'
        )
        self.locator_b = BlockUsageLocator(
            course_key=self.course_key,
            block_type='problem',
            block_id='block_id_b'
        )
        self.record_a = BlockRecord(unicode(self.locator_a), 1, 10)
        self.record_b = BlockRecord(unicode(self.locator_b), 1, 10)


@ddt.ddt
class BlockRecordTest(GradesModelTestCase):
    """
    Test the BlockRecord model.
    """
    def setUp(self):
        super(BlockRecordTest, self).setUp()

    def test_creation(self):
        """
        Tests creation of a BlockRecord.
        """
        weight = 1
        max_score = 10
        record = BlockRecord(
            self.locator_a,
            weight,
            max_score,
        )
        self.assertEqual(record.locator, self.locator_a)

    @ddt.data(
        (0, 0, "0123456789abcdef"),
        (1, 10, 'totally_a_real_block_key'),
        ("BlockRecord is", "a dumb data store", "with no validation"),
    )
    @ddt.unpack
    def test_serialization(self, weight, max_score, block_key):
        """
        Tests serialization of a BlockRecord using the to_dict() method.
        """
        record = BlockRecord(block_key, weight, max_score)
        expected = OrderedDict([
            ("locator", block_key),
            ("weight", weight),
            ("max_score", max_score),
        ])
        self.assertEqual(expected, record._asdict())


class VisibleBlocksTest(GradesModelTestCase):
    """
    Test the VisibleBlocks model.
    """
    def test_creation(self):
        """
        Happy path test to ensure basic create functionality works as expected.
        """
        vblocks = VisibleBlocks.objects.create_from_blockrecords([self.record_a])
        expected_json = json.dumps([self.record_a._asdict()], separators=(',', ':'), sort_keys=True)
        expected_hash = b64encode(sha256(expected_json).digest())
        self.assertEqual(expected_json, vblocks.blocks_json)
        self.assertEqual(expected_hash, vblocks.hashed)

    def test_ordering_does_not_matter(self):
        """
        When creating new vbocks, a different ordering of blocks produces the
        same record in the database.  
        """
        stored_vblocks = VisibleBlocks.objects.create_from_blockrecords([self.record_a, self.record_b])
        repeat_vblocks = VisibleBlocks.objects.create_from_blockrecords([self.record_b, self.record_a])
        new_vblocks = VisibleBlocks.objects.create_from_blockrecords([self.record_b])

        self.assertEqual(stored_vblocks.pk, repeat_vblocks.pk)
        self.assertEqual(stored_vblocks.hashed, repeat_vblocks.hashed)

        self.assertNotEqual(stored_vblocks.pk, new_vblocks.pk)
        self.assertNotEqual(stored_vblocks.hashed, new_vblocks.hashed)

    def test_blocks(self):
        """
        Ensures that, given an array of BlockRecord, creating visible_blocks and accessing visible_blocks.blocks yields
        a copy of the initial array. Also, trying to set the blocks property should raise an exception.
        """
        blocks = [self.record_a, self.record_b]
        vblocks = VisibleBlocks.objects.create_from_blockrecords(blocks)
        self.assertSequenceEqual(
            [block._asdict() for block in blocks],
            [block._asdict() for block in vblocks.blocks]
        )
        with self.assertRaises(AttributeError):
            vblocks.blocks = blocks


@ddt.ddt
class PersistentSubsectionGradeTest(GradesModelTestCase):
    """
    Test the PersistentSubsectionGrade model.
    """
    def setUp(self):
        super(PersistentSubsectionGradeTest, self).setUp()
        self.usage_key = BlockUsageLocator(
            course_key=self.course_key,
            block_type='subsection',
            block_id='subsection_12345',
        )
        self.params = {
            "user_id": 12345,
            "usage_key": self.usage_key,
            "course_version": "deadbeef",
            "subtree_edited_date": "2016-08-01 18:53:24.354741",
            "earned_all": 6,
            "possible_all": 12,
            "earned_graded": 6,
            "possible_graded": 8,
            "visible_blocks": [self.record_a, self.record_b],
        }

    def test_create(self):
        """
        Tests model creation, and confirms error when trying to recreate model.
        """
        created_grade = PersistentSubsectionGrade.objects.create(**self.params)
        read_grade = PersistentSubsectionGrade.read(user_id=self.params["user_id"], usage_key=self.params["usage_key"])
        self.assertEqual(created_grade, read_grade)
        with self.assertRaises(ValidationError):
            created_grade = PersistentSubsectionGrade.objects.create(**self.params)

    def test_create_bad_params(self):
        """
        Confirms create will fail if params are missing.
        """
        del self.params["course_version"]
        with self.assertRaises(ValidationError):
            PersistentSubsectionGrade.objects.create(**self.params)

    def test_update(self):
        """
        Tests model update, and confirms error when updating a nonexistent model.
        """
        with self.assertRaises(PersistentSubsectionGrade.DoesNotExist):
            PersistentSubsectionGrade.update(**self.params)
        PersistentSubsectionGrade.objects.create(**self.params)
        self.params['earned_all'] = 12
        self.params['earned_graded'] = 8
        PersistentSubsectionGrade.update(**self.params)
        read_grade = PersistentSubsectionGrade.read(user_id=self.params["user_id"], usage_key=self.params["usage_key"])
        self.assertEqual(read_grade.earned_all, 12)
        self.assertEqual(read_grade.earned_graded, 8)

    @ddt.data(True, False)
    def test_save(self, already_created):
        if already_created:
            PersistentSubsectionGrade.objects.create(**self.params)
        module_prefix = "lms.djangoapps.grades.models.PersistentSubsectionGrade."
        with patch(module_prefix + "objects.create") as mock_create:
            with patch(module_prefix + "update", wraps=PersistentSubsectionGrade.update) as mock_update:
                PersistentSubsectionGrade.save_grade(**self.params)
                self.assertTrue(mock_update.called)
                self.assertNotEqual(mock_create.called, already_created)
