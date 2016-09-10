"""
Unit tests for grades models.
"""
from base64 import b64encode
from collections import OrderedDict
import ddt
from hashlib import sha1
import json
from mock import patch

from django.db.utils import IntegrityError
from django.test import TestCase
from opaque_keys.edx.locator import CourseLocator, BlockUsageLocator

from lms.djangoapps.grades.models import (
    BlockRecord,
    BlockRecordList,
    PersistentSubsectionGrade,
    VisibleBlocks
)


class BlockRecordListTestCase(TestCase):
    """
    Verify the behavior of BlockRecordList, particularly around edge cases
    """
    empty_json = '{"blocks":[],"course_key":null}'

    def test_empty_block_record_set(self):
        brs = BlockRecordList(())
        self.assertFalse(brs)
        self.assertEqual(
            brs.to_json(),
            self.empty_json
        )
        self.assertEqual(
            BlockRecordList.from_json(self.empty_json),
            brs
        )


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
        self.record_a = BlockRecord(locator=self.locator_a, weight=1, max_score=10)
        self.record_b = BlockRecord(locator=self.locator_b, weight=1, max_score=10)


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
    def _create_block_record_list(self, blocks):
        """
        Creates and returns a BlockRecordList for the given blocks.
        """
        return VisibleBlocks.objects.create_from_blockrecords(BlockRecordList.from_list(blocks))

    def test_creation(self):
        """
        Happy path test to ensure basic create functionality works as expected.
        """
        vblocks = self._create_block_record_list([self.record_a])
        list_of_block_dicts = [self.record_a._asdict()]
        for block_dict in list_of_block_dicts:
            block_dict['locator'] = unicode(block_dict['locator'])  # BlockUsageLocator is not json-serializable
        expected_data = {
            'course_key': unicode(self.record_a.locator.course_key),
            'blocks': [
                {'locator': unicode(self.record_a.locator), 'max_score': 10, 'weight': 1},
            ],
        }
        expected_json = json.dumps(expected_data, separators=(',', ':'), sort_keys=True)
        expected_hash = b64encode(sha1(expected_json).digest())
        self.assertEqual(expected_data, json.loads(vblocks.blocks_json))
        self.assertEqual(expected_json, vblocks.blocks_json)
        self.assertEqual(expected_hash, vblocks.hashed)

    def test_ordering_matters(self):
        """
        When creating new vblocks, different ordering of blocks produces
        different records in the database.
        """
        stored_vblocks = self._create_block_record_list([self.record_a, self.record_b])
        repeat_vblocks = self._create_block_record_list([self.record_b, self.record_a])
        same_order_vblocks = self._create_block_record_list([self.record_a, self.record_b])
        new_vblocks = self._create_block_record_list([self.record_b])

        self.assertNotEqual(stored_vblocks.pk, repeat_vblocks.pk)
        self.assertNotEqual(stored_vblocks.hashed, repeat_vblocks.hashed)

        self.assertEquals(stored_vblocks.pk, same_order_vblocks.pk)
        self.assertEquals(stored_vblocks.hashed, same_order_vblocks.hashed)

        self.assertNotEqual(stored_vblocks.pk, new_vblocks.pk)
        self.assertNotEqual(stored_vblocks.hashed, new_vblocks.hashed)

    def test_blocks_property(self):
        """
        Ensures that, given an array of BlockRecord, creating visible_blocks
        and accessing visible_blocks.blocks yields a copy of the initial array.
        Also, trying to set the blocks property should raise an exception.
        """
        expected_blocks = (self.record_a, self.record_b)
        visible_blocks = self._create_block_record_list(expected_blocks)
        self.assertEqual(expected_blocks, visible_blocks.blocks)
        with self.assertRaises(AttributeError):
            visible_blocks.blocks = expected_blocks


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
            "subtree_edited_timestamp": "2016-08-01 18:53:24.354741",
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
        read_grade = PersistentSubsectionGrade.read_grade(
            user_id=self.params["user_id"],
            usage_key=self.params["usage_key"],
        )
        self.assertEqual(created_grade, read_grade)
        with self.assertRaises(IntegrityError):
            created_grade = PersistentSubsectionGrade.objects.create(**self.params)

    def test_create_bad_params(self):
        """
        Confirms create will fail if params are missing.
        """
        del self.params["earned_graded"]
        with self.assertRaises(IntegrityError):
            PersistentSubsectionGrade.objects.create(**self.params)

    def test_course_version_is_optional(self):
        del self.params["course_version"]
        PersistentSubsectionGrade.objects.create(**self.params)

    def test_update_grade(self):
        """
        Tests model update, and confirms error when updating a nonexistent model.
        """
        with self.assertRaises(PersistentSubsectionGrade.DoesNotExist):
            PersistentSubsectionGrade.update_grade(**self.params)
        PersistentSubsectionGrade.objects.create(**self.params)
        self.params['earned_all'] = 12
        self.params['earned_graded'] = 8
        PersistentSubsectionGrade.update_grade(**self.params)
        read_grade = PersistentSubsectionGrade.read_grade(
            user_id=self.params["user_id"],
            usage_key=self.params["usage_key"],
        )
        self.assertEqual(read_grade.earned_all, 12)
        self.assertEqual(read_grade.earned_graded, 8)

    @ddt.data(True, False)
    def test_save(self, already_created):
        if already_created:
            PersistentSubsectionGrade.objects.create(**self.params)
        module_prefix = "lms.djangoapps.grades.models.PersistentSubsectionGrade."
        with patch(
            module_prefix + "objects.get_or_create",
            wraps=PersistentSubsectionGrade.objects.get_or_create
        ) as mock_get_or_create:
            with patch(module_prefix + "update") as mock_update:
                PersistentSubsectionGrade.save_grade(**self.params)
                self.assertTrue(mock_get_or_create.called)
                self.assertEqual(mock_update.called, already_created)
