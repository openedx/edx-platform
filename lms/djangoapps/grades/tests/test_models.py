"""
Unit tests for grades models.
"""
import ddt
from hashlib import md5
import json
from mock import patch

from django.db.utils import IntegrityError
from django.test import TestCase
from opaque_keys import InvalidKeyError
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
        self.record_a = BlockRecord(1, 10, self.locator_a)
        self.record_b = BlockRecord(1, 10, self.locator_b)


@ddt.ddt
class BlockRecordTest(GradesModelTestCase):
    """
    Test the BlockRecord model.
    """
    def setUp(self):
        super(BlockRecordTest, self).setUp()

    @ddt.data(True, False)
    def test_creation(self, use_locator_as_string):
        """
        Tests creation of a BlockRecord, both with a locator object and its string representation.
        """
        weight = 1
        max_score = 10
        record = BlockRecord(
            weight,
            max_score,
            # pylint: disable=protected-access
            self.locator_a._to_string() if use_locator_as_string else self.locator_a
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
        record = BlockRecord(weight, max_score, block_key)
        expected = {
            "weight": weight,
            "max_score": max_score,
            "block_key": block_key,
        }
        self.assertEqual(expected, record.to_dict())

    def test_invalid_block_key(self):
        """
        Ensures invalid block keys throw an error when accessing a record's locator.
        """
        record = BlockRecord(1, 10, "not a block key at all")
        with self.assertRaises(InvalidKeyError):
            _ = record.locator


class VisibleBlocksTest(GradesModelTestCase):
    """
    Test the VisibleBlocks model.
    """
    def setUp(self):
        super(VisibleBlocksTest, self).setUp()

    def test_creation(self):
        """
        Happy path test to ensure basic create functionality works as expected.
        """
        vblocks = VisibleBlocks.create([self.record_a])
        expected_json = json.dumps([self.record_a.to_dict()])
        expected_hash = md5(expected_json).hexdigest()
        # pylint: disable=protected-access
        self.assertEqual(expected_json, vblocks._blocks_json)
        self.assertEqual(expected_hash, vblocks.hashed)

    def test_hashing(self):
        """
        Ensures that 2 BlockRecord arrays will yield the same hash, even if they're provided in a different order. Also
        ensures that creating a VisibleBlocks model with the same value as an existing one will yield a copy of the
        first object.
        """
        vblocks_a = VisibleBlocks.create([self.record_a, self.record_b])
        vblocks_b = VisibleBlocks.create([self.record_b, self.record_a])
        self.assertEqual(vblocks_a.hashed, vblocks_b.hashed)
        self.assertEqual(vblocks_a, vblocks_b)

    def test_blocks(self):
        """
        Ensures that, given an array of BlockRecord, creating visible_blocks and accessing visible_blocks.blocks yields
        a copy of the initial array. Also, trying to set the blocks property should raise an exception.
        """
        blocks = sorted(
            [self.record_a, self.record_b],
            key=lambda block: '{}{}{}'.format(block.block_key, block.max_score, block.weight)
        )
        vblocks = VisibleBlocks.create(blocks)
        self.assertSequenceEqual(
            [block.to_dict() for block in blocks],
            [block.to_dict() for block in vblocks.blocks]
        )
        with self.assertRaises(NotImplementedError):
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
            "user_id": "student12345",
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
        created_grade = PersistentSubsectionGrade.create(**self.params)
        read_grade = PersistentSubsectionGrade.read(user_id=self.params["user_id"], usage_key=self.params["usage_key"])
        self.assertEqual(created_grade, read_grade)
        with self.assertRaises(IntegrityError):
            created_grade = PersistentSubsectionGrade.create(**self.params)

    @ddt.data(
        ("missing", KeyError),
        ("invalid", AttributeError),
    )
    @ddt.unpack
    def test_create_bad_params(self, ddt_name, error):
        """
        Confirms create will fail if params are missing or invalid.
        """
        if ddt_name == "missing":
            del self.params["course_version"]
        elif ddt_name == "invalid":
            self.params["usage_key"] = "usage_keys_are_strings_now"
        with self.assertRaises(error):
            _ = PersistentSubsectionGrade.create(**self.params)

    def test_update(self):
        """
        Tests model update, and confirms error when updating a nonexistent model.
        """
        with self.assertRaises(PersistentSubsectionGrade.DoesNotExist):
            PersistentSubsectionGrade.update(**self.params)
        _ = PersistentSubsectionGrade.create(**self.params)
        self.params['earned_all'] = 12
        self.params['earned_graded'] = 8
        PersistentSubsectionGrade.update(**self.params)
        read_grade = PersistentSubsectionGrade.read(user_id=self.params["user_id"], usage_key=self.params["usage_key"])
        self.assertEqual(read_grade.earned_all, 12)
        self.assertEqual(read_grade.earned_graded, 8)

    @ddt.data(True, False)
    def test_save(self, already_created):
        if already_created:
            _ = PersistentSubsectionGrade.create(**self.params)
            mock_fn_called = "update"
            mock_fn_uncalled = "create"
        else:
            mock_fn_called = "update"
            mock_fn_uncalled = "create"
        with patch("lms.djangoapps.grades.models.PersistentSubsectionGrade." + mock_fn_called) as mock_called:
            with patch("lms.djangoapps.grades.models.PersistentSubsectionGrade." + mock_fn_uncalled) as mock_uncalled:
                PersistentSubsectionGrade.save_grade()
                self.assertTrue(mock_called.called)
                self.assertFalse(mock_uncalled.called)
