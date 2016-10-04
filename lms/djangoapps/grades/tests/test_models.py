"""
Unit tests for grades models.
"""
from base64 import b64encode
from collections import OrderedDict
import ddt
from hashlib import sha1
import json

from django.db.utils import IntegrityError
from django.test import TestCase
from opaque_keys.edx.locator import CourseLocator, BlockUsageLocator

from lms.djangoapps.grades.models import (
    BlockRecord,
    BlockRecordList,
    BLOCK_RECORD_LIST_VERSION,
    PersistentSubsectionGrade,
    VisibleBlocks
)


class BlockRecordListTestCase(TestCase):
    """
    Verify the behavior of BlockRecordList, particularly around edge cases
    """
    def setUp(self):
        super(BlockRecordListTestCase, self).setUp()
        self.course_key = CourseLocator(
            org='some_org',
            course='some_course',
            run='some_run'
        )

    def test_empty_block_record_set(self):
        empty_json = u'{"blocks":[],"course_key":"%s","version":%s}' % (
            unicode(self.course_key),
            BLOCK_RECORD_LIST_VERSION,
        )

        brs = BlockRecordList((), self.course_key)
        self.assertFalse(brs)
        self.assertEqual(
            brs.json_value,
            empty_json
        )
        self.assertEqual(
            BlockRecordList.from_json(empty_json),
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
        self.record_a = BlockRecord(locator=self.locator_a, weight=1, raw_possible=10, graded=False)
        self.record_b = BlockRecord(locator=self.locator_b, weight=1, raw_possible=10, graded=True)


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
        raw_possible = 10
        record = BlockRecord(
            self.locator_a,
            weight,
            raw_possible,
            graded=False,
        )
        self.assertEqual(record.locator, self.locator_a)

    @ddt.data(
        (0, 0, "0123456789abcdef", True),
        (1, 10, 'totally_a_real_block_key', False),
        ("BlockRecord is", "a dumb data store", "with no validation", None),
    )
    @ddt.unpack
    def test_serialization(self, weight, raw_possible, block_key, graded):
        """
        Tests serialization of a BlockRecord using the _asdict() method.
        """
        record = BlockRecord(block_key, weight, raw_possible, graded)
        expected = OrderedDict([
            ("locator", block_key),
            ("weight", weight),
            ("raw_possible", raw_possible),
            ("graded", graded),
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
        return VisibleBlocks.objects.create_from_blockrecords(BlockRecordList.from_list(blocks, self.course_key))

    def test_creation(self):
        """
        Happy path test to ensure basic create functionality works as expected.
        """
        vblocks = self._create_block_record_list([self.record_a])
        list_of_block_dicts = [self.record_a._asdict()]
        for block_dict in list_of_block_dicts:
            block_dict['locator'] = unicode(block_dict['locator'])  # BlockUsageLocator is not json-serializable
        expected_data = {
            'blocks': [{
                'locator': unicode(self.record_a.locator),
                'raw_possible': 10,
                'weight': 1,
                'graded': self.record_a.graded,
            }],
            'course_key': unicode(self.record_a.locator.course_key),
            'version': BLOCK_RECORD_LIST_VERSION,
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
        expected_blocks = BlockRecordList.from_list([self.record_a, self.record_b], self.course_key)
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
        self.block_records = BlockRecordList([self.record_a, self.record_b], self.course_key)
        self.params = {
            "user_id": 12345,
            "usage_key": self.usage_key,
            "course_version": "deadbeef",
            "subtree_edited_timestamp": "2016-08-01 18:53:24.354741",
            "earned_all": 6.0,
            "possible_all": 12.0,
            "earned_graded": 6.0,
            "possible_graded": 8.0,
            "visible_blocks": self.block_records,
        }

    def test_create(self):
        """
        Tests model creation, and confirms error when trying to recreate model.
        """
        created_grade = PersistentSubsectionGrade.create_grade(**self.params)
        with self.assertNumQueries(1):
            read_grade = PersistentSubsectionGrade.read_grade(
                user_id=self.params["user_id"],
                usage_key=self.params["usage_key"],
            )
            self.assertEqual(created_grade, read_grade)
            self.assertEquals(read_grade.visible_blocks.blocks, self.block_records)
        with self.assertRaises(IntegrityError):
            PersistentSubsectionGrade.create_grade(**self.params)

    def test_create_bad_params(self):
        """
        Confirms create will fail if params are missing.
        """
        del self.params["earned_graded"]
        with self.assertRaises(IntegrityError):
            PersistentSubsectionGrade.create_grade(**self.params)

    def test_course_version_is_optional(self):
        del self.params["course_version"]
        PersistentSubsectionGrade.create_grade(**self.params)

    @ddt.data(True, False)
    def test_update_or_create_grade(self, already_created):
        created_grade = PersistentSubsectionGrade.create_grade(**self.params) if already_created else None

        self.params["earned_all"] = 7
        updated_grade = PersistentSubsectionGrade.update_or_create_grade(**self.params)
        self.assertEquals(updated_grade.earned_all, 7)
        if already_created:
            self.assertEquals(created_grade.id, updated_grade.id)
            self.assertEquals(created_grade.earned_all, 6)
