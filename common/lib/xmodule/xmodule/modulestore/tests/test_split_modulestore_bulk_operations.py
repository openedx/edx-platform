import copy
import ddt
import unittest
from bson.objectid import ObjectId
from mock import MagicMock, Mock, call
from xmodule.modulestore.split_mongo.split import BulkWriteMixin
from xmodule.modulestore.split_mongo.mongo_connection import MongoConnection

from opaque_keys.edx.locator import CourseLocator, BlockUsageLocator, VersionTree, LocalId


class TestBulkWriteMixin(unittest.TestCase):
    def setUp(self):
        super(TestBulkWriteMixin, self).setUp()
        self.bulk = BulkWriteMixin()
        self.clear_cache = self.bulk._clear_cache = Mock(name='_clear_cache')
        self.conn = self.bulk.db_connection = MagicMock(name='db_connection', spec=MongoConnection)

        self.course_key = CourseLocator('org', 'course', 'run-a')
        self.course_key_b = CourseLocator('org', 'course', 'run-b')
        self.structure = {'this': 'is', 'a': 'structure', '_id': ObjectId()}
        self.index_entry = {'this': 'is', 'an': 'index'}

    def assertConnCalls(self, *calls):
        self.assertEqual(list(calls), self.conn.mock_calls)

    def assertCacheNotCleared(self):
        self.assertFalse(self.clear_cache.called)


class TestBulkWriteMixinPreviousTransaction(TestBulkWriteMixin):
    """
    Verify that opening and closing a transaction doesn't affect later behaviour.
    """
    def setUp(self):
        super(TestBulkWriteMixinPreviousTransaction, self).setUp()
        self.bulk._begin_bulk_write_operation(self.course_key)
        self.bulk.insert_course_index(self.course_key, MagicMock('prev-index-entry'))
        self.bulk.update_structure(self.course_key, {'this': 'is', 'the': 'previous structure', '_id': ObjectId()})
        self.bulk._end_bulk_write_operation(self.course_key)
        self.conn.reset_mock()
        self.clear_cache.reset_mock()


@ddt.ddt
class TestBulkWriteMixinClosed(TestBulkWriteMixin):
    """
    Tests of the bulk write mixin when bulk operations aren't active.
    """
    @ddt.data('deadbeef1234' * 2, u'deadbeef1234' * 2, ObjectId())
    def test_no_bulk_read_structure(self, version_guid):
        # Reading a structure when no bulk operation is active should just call
        # through to the db_connection
        result = self.bulk.get_structure(self.course_key, version_guid)
        self.assertConnCalls(call.get_structure(self.course_key.as_object_id(version_guid)))
        self.assertEqual(result, self.conn.get_structure.return_value)
        self.assertCacheNotCleared()

    def test_no_bulk_write_structure(self):
        # Writing a structure when no bulk operation is active should just
        # call through to the db_connection. It should also clear the
        # system cache
        self.bulk.update_structure(self.course_key, self.structure)
        self.assertConnCalls(call.upsert_structure(self.structure))
        self.clear_cache.assert_called_once_with(self.structure['_id'])

    @ddt.data(True, False)
    def test_no_bulk_read_index(self, ignore_case):
        # Reading a course index when no bulk operation is active should just call
        # through to the db_connection
        result = self.bulk.get_course_index(self.course_key, ignore_case=ignore_case)
        self.assertConnCalls(call.get_course_index(self.course_key, ignore_case))
        self.assertEqual(result, self.conn.get_course_index.return_value)
        self.assertCacheNotCleared()

    def test_no_bulk_write_index(self):
        # Writing a course index when no bulk operation is active should just call
        # through to the db_connection
        self.bulk.insert_course_index(self.course_key, self.index_entry)
        self.assertConnCalls(call.insert_course_index(self.index_entry))
        self.assertCacheNotCleared()

    def test_out_of_order_end(self):
        # Calling _end_bulk_write_operation without a corresponding _begin...
        # is a noop
        self.bulk._end_bulk_write_operation(self.course_key)

    def test_write_new_index_on_close(self):
        self.conn.get_course_index.return_value = None
        self.bulk._begin_bulk_write_operation(self.course_key)
        self.conn.reset_mock()
        self.bulk.insert_course_index(self.course_key, self.index_entry)
        self.assertConnCalls()
        self.bulk._end_bulk_write_operation(self.course_key)
        self.conn.insert_course_index.assert_called_once_with(self.index_entry)

    def test_write_updated_index_on_close(self):
        old_index = {'this': 'is', 'an': 'old index'}
        self.conn.get_course_index.return_value = old_index
        self.bulk._begin_bulk_write_operation(self.course_key)
        self.conn.reset_mock()
        self.bulk.insert_course_index(self.course_key, self.index_entry)
        self.assertConnCalls()
        self.bulk._end_bulk_write_operation(self.course_key)
        self.conn.update_course_index.assert_called_once_with(self.index_entry, from_index=old_index)

    def test_write_structure_on_close(self):
        self.conn.get_course_index.return_value = None
        self.bulk._begin_bulk_write_operation(self.course_key)
        self.conn.reset_mock()
        self.bulk.update_structure(self.course_key, self.structure)
        self.assertConnCalls()
        self.bulk._end_bulk_write_operation(self.course_key)
        self.assertConnCalls(call.insert_structure(self.structure))

    def test_write_multiple_structures_on_close(self):
        self.conn.get_course_index.return_value = None
        self.bulk._begin_bulk_write_operation(self.course_key)
        self.conn.reset_mock()
        self.bulk.update_structure(self.course_key.replace(branch='a'), self.structure)
        other_structure = {'another': 'structure', '_id': ObjectId()}
        self.bulk.update_structure(self.course_key.replace(branch='b'), other_structure)
        self.assertConnCalls()
        self.bulk._end_bulk_write_operation(self.course_key)
        self.assertItemsEqual(
            [call.insert_structure(self.structure), call.insert_structure(other_structure)],
            self.conn.mock_calls
        )

    def test_write_index_and_structure_on_close(self):
        original_index = {'versions': {}}
        self.conn.get_course_index.return_value = copy.deepcopy(original_index)
        self.bulk._begin_bulk_write_operation(self.course_key)
        self.conn.reset_mock()
        self.bulk.update_structure(self.course_key, self.structure)
        self.assertConnCalls()
        self.bulk._end_bulk_write_operation(self.course_key)
        self.assertConnCalls(
            call.insert_structure(self.structure),
            call.update_course_index(
                {'versions': {self.course_key.branch: self.structure['_id']}},
                from_index=original_index
            )
        )

    def test_write_index_and_multiple_structures_on_close(self):
        original_index = {'versions': {'a': ObjectId(), 'b': ObjectId()}}
        self.conn.get_course_index.return_value = copy.deepcopy(original_index)
        self.bulk._begin_bulk_write_operation(self.course_key)
        self.conn.reset_mock()
        self.bulk.update_structure(self.course_key.replace(branch='a'), self.structure)
        other_structure = {'another': 'structure', '_id': ObjectId()}
        self.bulk.update_structure(self.course_key.replace(branch='b'), other_structure)
        self.assertConnCalls()
        self.bulk._end_bulk_write_operation(self.course_key)
        self.assertItemsEqual(
            [
                call.insert_structure(self.structure),
                call.insert_structure(other_structure),
                call.update_course_index(
                    {'versions': {'a': self.structure['_id'], 'b': other_structure['_id']}},
                    from_index=original_index
                )
            ],
            self.conn.mock_calls
        )

class TestBulkWriteMixinClosedAfterPrevTransaction(TestBulkWriteMixinClosed, TestBulkWriteMixinPreviousTransaction):
    """
    Test that operations on with a closed transaction aren't affected by a previously executed transaction
    """
    pass


@ddt.ddt
class TestBulkWriteMixinOpen(TestBulkWriteMixin):
    """
    Tests of the bulk write mixin when bulk write operations are open
    """
    def setUp(self):
        super(TestBulkWriteMixinOpen, self).setUp()
        self.bulk._begin_bulk_write_operation(self.course_key)

    @ddt.data('deadbeef1234' * 2, u'deadbeef1234' * 2, ObjectId())
    def test_read_structure_without_write_from_db(self, version_guid):
        # Reading a structure before it's been written (while in bulk operation mode)
        # returns the structure from the database
        result = self.bulk.get_structure(self.course_key, version_guid)
        self.assertEquals(self.conn.get_structure.call_count, 1)
        self.assertEqual(result, self.conn.get_structure.return_value)
        self.assertCacheNotCleared()

    @ddt.data('deadbeef1234' * 2, u'deadbeef1234' * 2, ObjectId())
    def test_read_structure_without_write_only_reads_once(self, version_guid):
        # Reading the same structure multiple times shouldn't hit the database
        # more than once
        for _ in xrange(2):
            result = self.bulk.get_structure(self.course_key, version_guid)
            self.assertEquals(self.conn.get_structure.call_count, 1)
            self.assertEqual(result, self.conn.get_structure.return_value)
            self.assertCacheNotCleared()

    @ddt.data('deadbeef1234' * 2, u'deadbeef1234' * 2, ObjectId())
    def test_read_structure_after_write_no_db(self, version_guid):
        # Reading a structure that's already been written shouldn't hit the db at all
        self.bulk.update_structure(self.course_key, self.structure)
        result = self.bulk.get_structure(self.course_key, version_guid)
        self.assertEquals(self.conn.get_structure.call_count, 0)
        self.assertEqual(result, self.structure)

    @ddt.data('deadbeef1234' * 2, u'deadbeef1234' * 2, ObjectId())
    def test_read_structure_after_write_after_read(self, version_guid):
        # Reading a structure that's been updated after being pulled from the db should
        # still get the updated value
        result = self.bulk.get_structure(self.course_key, version_guid)
        self.bulk.update_structure(self.course_key, self.structure)
        result = self.bulk.get_structure(self.course_key, version_guid)
        self.assertEquals(self.conn.get_structure.call_count, 1)
        self.assertEqual(result, self.structure)

    @ddt.data(True, False)
    def test_read_index_without_write_from_db(self, ignore_case):
        # Reading the index without writing to it should pull from the database
        result = self.bulk.get_course_index(self.course_key, ignore_case=ignore_case)
        self.assertEquals(self.conn.get_course_index.call_count, 1)
        self.assertEquals(self.conn.get_course_index.return_value, result)

    @ddt.data(True, False)
    def test_read_index_without_write_only_reads_once(self, ignore_case):
        # Reading the index multiple times should only result in one read from
        # the database
        for _ in xrange(2):
            result = self.bulk.get_course_index(self.course_key, ignore_case=ignore_case)
            self.assertEquals(self.conn.get_course_index.call_count, 1)
            self.assertEquals(self.conn.get_course_index.return_value, result)

    @ddt.data(True, False)
    def test_read_index_after_write(self, ignore_case):
        # Reading the index after a write still should hit the database once to fetch the
        # initial index, and should return the written index_entry
        self.bulk.insert_course_index(self.course_key, self.index_entry)
        result = self.bulk.get_course_index(self.course_key, ignore_case=ignore_case)
        self.assertEquals(self.conn.get_course_index.call_count, 1)
        self.assertEquals(self.index_entry, result)

    def test_read_index_ignore_case(self):
        # Reading using ignore case should find an already written entry with a different case
        self.bulk.insert_course_index(self.course_key, self.index_entry)
        result = self.bulk.get_course_index(
            self.course_key.replace(
                org=self.course_key.org.upper(),
                course=self.course_key.course.title(),
                run=self.course_key.run.upper()
            ),
            ignore_case=True
        )
        self.assertEquals(self.conn.get_course_index.call_count, 1)
        self.assertEquals(self.index_entry, result)



class TestBulkWriteMixinOpenAfterPrevTransaction(TestBulkWriteMixinOpen, TestBulkWriteMixinPreviousTransaction):
    """
    Test that operations on with an open transaction aren't affected by a previously executed transaction
    """
    pass
