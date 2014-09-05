import copy
import ddt
import unittest
from bson.objectid import ObjectId
from mock import MagicMock, Mock, call
from xmodule.modulestore.split_mongo.split import SplitBulkWriteMixin
from xmodule.modulestore.split_mongo.mongo_connection import MongoConnection

from opaque_keys.edx.locator import CourseLocator


class TestBulkWriteMixin(unittest.TestCase):
    def setUp(self):
        super(TestBulkWriteMixin, self).setUp()
        self.bulk = SplitBulkWriteMixin()
        self.bulk.SCHEMA_VERSION = 1
        self.clear_cache = self.bulk._clear_cache = Mock(name='_clear_cache')
        self.conn = self.bulk.db_connection = MagicMock(name='db_connection', spec=MongoConnection)
        self.conn.get_course_index.return_value = {'initial': 'index'}

        self.course_key = CourseLocator('org', 'course', 'run-a', branch='test')
        self.course_key_b = CourseLocator('org', 'course', 'run-b', branch='test')
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
        self.bulk._begin_bulk_operation(self.course_key)
        self.bulk.insert_course_index(self.course_key, MagicMock('prev-index-entry'))
        self.bulk.update_structure(self.course_key, {'this': 'is', 'the': 'previous structure', '_id': ObjectId()})
        self.bulk._end_bulk_operation(self.course_key)
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
        # Calling _end_bulk_operation without a corresponding _begin...
        # is a noop
        self.bulk._end_bulk_operation(self.course_key)

    def test_write_new_index_on_close(self):
        self.conn.get_course_index.return_value = None
        self.bulk._begin_bulk_operation(self.course_key)
        self.conn.reset_mock()
        self.bulk.insert_course_index(self.course_key, self.index_entry)
        self.assertConnCalls()
        self.bulk._end_bulk_operation(self.course_key)
        self.conn.insert_course_index.assert_called_once_with(self.index_entry)

    def test_write_updated_index_on_close(self):
        old_index = {'this': 'is', 'an': 'old index'}
        self.conn.get_course_index.return_value = old_index
        self.bulk._begin_bulk_operation(self.course_key)
        self.conn.reset_mock()
        self.bulk.insert_course_index(self.course_key, self.index_entry)
        self.assertConnCalls()
        self.bulk._end_bulk_operation(self.course_key)
        self.conn.update_course_index.assert_called_once_with(self.index_entry, from_index=old_index)

    def test_write_structure_on_close(self):
        self.conn.get_course_index.return_value = None
        self.bulk._begin_bulk_operation(self.course_key)
        self.conn.reset_mock()
        self.bulk.update_structure(self.course_key, self.structure)
        self.assertConnCalls()
        self.bulk._end_bulk_operation(self.course_key)
        self.assertConnCalls(call.upsert_structure(self.structure))

    def test_write_multiple_structures_on_close(self):
        self.conn.get_course_index.return_value = None
        self.bulk._begin_bulk_operation(self.course_key)
        self.conn.reset_mock()
        self.bulk.update_structure(self.course_key.replace(branch='a'), self.structure)
        other_structure = {'another': 'structure', '_id': ObjectId()}
        self.bulk.update_structure(self.course_key.replace(branch='b'), other_structure)
        self.assertConnCalls()
        self.bulk._end_bulk_operation(self.course_key)
        self.assertItemsEqual(
            [call.upsert_structure(self.structure), call.upsert_structure(other_structure)],
            self.conn.mock_calls
        )

    def test_write_index_and_structure_on_close(self):
        original_index = {'versions': {}}
        self.conn.get_course_index.return_value = copy.deepcopy(original_index)
        self.bulk._begin_bulk_operation(self.course_key)
        self.conn.reset_mock()
        self.bulk.update_structure(self.course_key, self.structure)
        self.bulk.insert_course_index(self.course_key, {'versions': {self.course_key.branch: self.structure['_id']}})
        self.assertConnCalls()
        self.bulk._end_bulk_operation(self.course_key)
        self.assertConnCalls(
            call.upsert_structure(self.structure),
            call.update_course_index(
                {'versions': {self.course_key.branch: self.structure['_id']}},
                from_index=original_index
            )
        )

    def test_write_index_and_multiple_structures_on_close(self):
        original_index = {'versions': {'a': ObjectId(), 'b': ObjectId()}}
        self.conn.get_course_index.return_value = copy.deepcopy(original_index)
        self.bulk._begin_bulk_operation(self.course_key)
        self.conn.reset_mock()
        self.bulk.update_structure(self.course_key.replace(branch='a'), self.structure)
        other_structure = {'another': 'structure', '_id': ObjectId()}
        self.bulk.update_structure(self.course_key.replace(branch='b'), other_structure)
        self.bulk.insert_course_index(self.course_key, {'versions': {'a': self.structure['_id'], 'b': other_structure['_id']}})
        self.bulk._end_bulk_operation(self.course_key)
        self.assertItemsEqual(
            [
                call.upsert_structure(self.structure),
                call.upsert_structure(other_structure),
                call.update_course_index(
                    {'versions': {'a': self.structure['_id'], 'b': other_structure['_id']}},
                    from_index=original_index
                )
            ],
            self.conn.mock_calls
        )

    def test_version_structure_creates_new_version(self):
        self.assertNotEquals(
            self.bulk.version_structure(self.course_key, self.structure, 'user_id')['_id'],
            self.structure['_id']
        )

    def test_version_structure_new_course(self):
        self.conn.get_course_index.return_value = None
        self.bulk._begin_bulk_operation(self.course_key)
        version_result = self.bulk.version_structure(self.course_key, self.structure, 'user_id')
        get_result = self.bulk.get_structure(self.course_key, version_result['_id'])
        self.assertEquals(version_result, get_result)

class TestBulkWriteMixinClosedAfterPrevTransaction(TestBulkWriteMixinClosed, TestBulkWriteMixinPreviousTransaction):
    """
    Test that operations on with a closed transaction aren't affected by a previously executed transaction
    """
    pass


@ddt.ddt
class TestBulkWriteMixinFindMethods(TestBulkWriteMixin):
    """
    Tests of BulkWriteMixin methods for finding many structures or indexes
    """
    def test_no_bulk_find_matching_course_indexes(self):
        branch = Mock(name='branch')
        search_targets = MagicMock(name='search_targets')
        self.conn.find_matching_course_indexes.return_value = [Mock(name='result')]
        result = self.bulk.find_matching_course_indexes(branch, search_targets)
        self.assertConnCalls(call.find_matching_course_indexes(branch, search_targets))
        self.assertEqual(result, self.conn.find_matching_course_indexes.return_value)
        self.assertCacheNotCleared()

    @ddt.data(
        (None, None, [], []),
        (
            'draft',
            None,
            [{'versions': {'draft': '123'}}],
            [
                {'versions': {'published': '123'}},
                {}
            ],
        ),
        (
            'draft',
            {'f1': 'v1'},
            [{'versions': {'draft': '123'}, 'search_targets': {'f1': 'v1'}}],
            [
                {'versions': {'draft': '123'}, 'search_targets': {'f1': 'value2'}},
                {'versions': {'published': '123'}, 'search_targets': {'f1': 'v1'}},
                {'search_targets': {'f1': 'v1'}},
                {'versions': {'draft': '123'}},
            ],
        ),
        (
            None,
            {'f1': 'v1'},
            [
                {'versions': {'draft': '123'}, 'search_targets': {'f1': 'v1'}},
                {'versions': {'published': '123'}, 'search_targets': {'f1': 'v1'}},
                {'search_targets': {'f1': 'v1'}},
            ],
            [
                {'versions': {'draft': '123'}, 'search_targets': {'f1': 'v2'}},
                {'versions': {'draft': '123'}, 'search_targets': {'f2': 'v1'}},
                {'versions': {'draft': '123'}},
            ],
        ),
        (
            None,
            {'f1': 'v1', 'f2': 2},
            [
                {'search_targets': {'f1': 'v1', 'f2': 2}},
                {'search_targets': {'f1': 'v1', 'f2': 2}},
            ],
            [
                {'versions': {'draft': '123'}, 'search_targets': {'f1': 'v1'}},
                {'search_targets': {'f1': 'v1'}},
                {'versions': {'draft': '123'}, 'search_targets': {'f1': 'v2'}},
                {'versions': {'draft': '123'}},
            ],
        ),
    )
    @ddt.unpack
    def test_find_matching_course_indexes(self, branch, search_targets, matching, unmatching):
        db_indexes = [Mock(name='from_db')]
        for n, index in enumerate(matching + unmatching):
            course_key = CourseLocator('org', 'course', 'run{}'.format(n))
            self.bulk._begin_bulk_operation(course_key)
            self.bulk.insert_course_index(course_key, index)

        expected = matching + db_indexes
        self.conn.find_matching_course_indexes.return_value = db_indexes
        result = self.bulk.find_matching_course_indexes(branch, search_targets)
        self.assertItemsEqual(result, expected)
        for item in unmatching:
            self.assertNotIn(item, result)

    def test_no_bulk_find_structures_by_id(self):
        ids = [Mock(name='id')]
        self.conn.find_structures_by_id.return_value = [MagicMock(name='result')]
        result = self.bulk.find_structures_by_id(ids)
        self.assertConnCalls(call.find_structures_by_id(ids))
        self.assertEqual(result, self.conn.find_structures_by_id.return_value)
        self.assertCacheNotCleared()

    @ddt.data(
        ([], [], []),
        ([1, 2, 3], [1, 2], [1, 2]),
        ([1, 2, 3], [1], [1, 2]),
        ([1, 2, 3], [], [1, 2]),
    )
    @ddt.unpack
    def test_find_structures_by_id(self, search_ids, active_ids, db_ids):
        db_structure = lambda _id: {'db': 'structure', '_id': _id}
        active_structure = lambda _id: {'active': 'structure', '_id': _id}

        db_structures = [db_structure(_id) for _id in db_ids if _id not in active_ids]
        for n, _id in enumerate(active_ids):
            course_key = CourseLocator('org', 'course', 'run{}'.format(n))
            self.bulk._begin_bulk_operation(course_key)
            self.bulk.update_structure(course_key, active_structure(_id))

        self.conn.find_structures_by_id.return_value = db_structures
        results = self.bulk.find_structures_by_id(search_ids)
        self.conn.find_structures_by_id.assert_called_once_with(list(set(search_ids) - set(active_ids)))
        for _id in active_ids:
            if _id in search_ids:
                self.assertIn(active_structure(_id), results)
            else:
                self.assertNotIn(active_structure(_id), results)
        for _id in db_ids:
            if _id in search_ids and _id not in active_ids:
                self.assertIn(db_structure(_id), results)
            else:
                self.assertNotIn(db_structure(_id), results)

    def test_no_bulk_find_structures_derived_from(self):
        ids = [Mock(name='id')]
        self.conn.find_structures_derived_from.return_value = [MagicMock(name='result')]
        result = self.bulk.find_structures_derived_from(ids)
        self.assertConnCalls(call.find_structures_derived_from(ids))
        self.assertEqual(result, self.conn.find_structures_derived_from.return_value)
        self.assertCacheNotCleared()

    @ddt.data(
        # Test values are:
        #   - previous_versions to search for
        #   - documents in the cache with $previous_version.$_id
        #   - documents in the db with $previous_version.$_id
        ([], [], []),
        (['1', '2', '3'], ['1.a', '1.b', '2.c'], ['1.a', '2.c']),
        (['1', '2', '3'], ['1.a'], ['1.a', '2.c']),
        (['1', '2', '3'], [], ['1.a', '2.c']),
        (['1', '2', '3'], ['4.d'], ['1.a', '2.c']),
    )
    @ddt.unpack
    def test_find_structures_derived_from(self, search_ids, active_ids, db_ids):
        def db_structure(_id):
            previous, _, current = _id.partition('.')
            return {'db': 'structure', 'previous_version': previous, '_id': current}
        def active_structure(_id):
            previous, _, current = _id.partition('.')
            return {'active': 'structure', 'previous_version': previous, '_id': current}

        db_structures = [db_structure(_id) for _id in db_ids]
        active_structures = []
        for n, _id in enumerate(active_ids):
            course_key = CourseLocator('org', 'course', 'run{}'.format(n))
            self.bulk._begin_bulk_operation(course_key)
            structure = active_structure(_id)
            self.bulk.update_structure(course_key, structure)
            active_structures.append(structure)

        self.conn.find_structures_derived_from.return_value = db_structures
        results = self.bulk.find_structures_derived_from(search_ids)
        self.conn.find_structures_derived_from.assert_called_once_with(search_ids)
        for structure in active_structures:
            if structure['previous_version'] in search_ids:
                self.assertIn(structure, results)
            else:
                self.assertNotIn(structure, results)
        for structure in db_structures:
            if (
                structure['previous_version'] in search_ids and  # We're searching for this document
                not any(active.endswith(structure['_id']) for active in active_ids)  # This document doesn't match any active _ids
            ):
                self.assertIn(structure, results)
            else:
                self.assertNotIn(structure, results)

    def test_no_bulk_find_ancestor_structures(self):
        original_version = Mock(name='original_version')
        block_id = Mock(name='block_id')
        self.conn.find_ancestor_structures.return_value = [MagicMock(name='result')]
        result = self.bulk.find_ancestor_structures(original_version, block_id)
        self.assertConnCalls(call.find_ancestor_structures(original_version, block_id))
        self.assertEqual(result, self.conn.find_ancestor_structures.return_value)
        self.assertCacheNotCleared()

    @ddt.data(
        # Test values are:
        #   - original_version
        #   - block_id
        #   - matching documents in the cache
        #   - non-matching documents in the cache
        #   - expected documents returned from the db
        #   - unexpected documents returned from the db
        ('ov', 'bi', [{'original_version': 'ov', 'blocks': {'bi': {'edit_info': {'update_version': 'foo'}}}}], [], [], []),
        ('ov', 'bi', [{'original_version': 'ov', 'blocks': {'bi': {'edit_info': {'update_version': 'foo'}}}, '_id': 'foo'}], [], [], [{'_id': 'foo'}]),
        ('ov', 'bi', [], [{'blocks': {'bi': {'edit_info': {'update_version': 'foo'}}}}], [], []),
        ('ov', 'bi', [], [{'original_version': 'ov'}], [], []),
        ('ov', 'bi', [], [], [{'original_version': 'ov', 'blocks': {'bi': {'edit_info': {'update_version': 'foo'}}}}], []),
        (
            'ov',
            'bi',
            [{'original_version': 'ov', 'blocks': {'bi': {'edit_info': {'update_version': 'foo'}}}}],
            [],
            [{'original_version': 'ov', 'blocks': {'bi': {'edit_info': {'update_version': 'bar'}}}}],
            []
        ),
    )
    @ddt.unpack
    def test_find_ancestor_structures(self, original_version, block_id, active_match, active_unmatch, db_match, db_unmatch):
        for structure in active_match + active_unmatch + db_match + db_unmatch:
            structure.setdefault('_id', ObjectId())

        for n, structure in enumerate(active_match + active_unmatch):
            course_key = CourseLocator('org', 'course', 'run{}'.format(n))
            self.bulk._begin_bulk_operation(course_key)
            self.bulk.update_structure(course_key, structure)

        self.conn.find_ancestor_structures.return_value = db_match + db_unmatch
        results = self.bulk.find_ancestor_structures(original_version, block_id)
        self.conn.find_ancestor_structures.assert_called_once_with(original_version, block_id)
        self.assertItemsEqual(active_match + db_match, results)


@ddt.ddt
class TestBulkWriteMixinOpen(TestBulkWriteMixin):
    """
    Tests of the bulk write mixin when bulk write operations are open
    """
    def setUp(self):
        super(TestBulkWriteMixinOpen, self).setUp()
        self.bulk._begin_bulk_operation(self.course_key)

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
        self.structure['_id'] = version_guid
        self.bulk.update_structure(self.course_key, self.structure)
        result = self.bulk.get_structure(self.course_key, version_guid)
        self.assertEquals(self.conn.get_structure.call_count, 0)
        self.assertEqual(result, self.structure)

    @ddt.data('deadbeef1234' * 2, u'deadbeef1234' * 2, ObjectId())
    def test_read_structure_after_write_after_read(self, version_guid):
        # Reading a structure that's been updated after being pulled from the db should
        # still get the updated value
        self.structure['_id'] = version_guid
        self.bulk.get_structure(self.course_key, version_guid)
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

    def test_version_structure_creates_new_version_before_read(self):
        self.assertNotEquals(
            self.bulk.version_structure(self.course_key, self.structure, 'user_id')['_id'],
            self.structure['_id']
        )

    def test_version_structure_creates_new_version_after_read(self):
        self.conn.get_structure.return_value = copy.deepcopy(self.structure)
        self.bulk.get_structure(self.course_key, self.structure['_id'])
        self.assertNotEquals(
            self.bulk.version_structure(self.course_key, self.structure, 'user_id')['_id'],
            self.structure['_id']
        )

    def test_copy_branch_versions(self):
        # Directly updating an index so that the draft branch points to the published index
        # version should work, and should only persist a single structure
        self.maxDiff = None
        published_structure = {'published': 'structure', '_id': ObjectId()}
        self.bulk.update_structure(self.course_key, published_structure)
        index = {'versions': {'published': published_structure['_id']}}
        self.bulk.insert_course_index(self.course_key, index)
        index_copy = copy.deepcopy(index)
        index_copy['versions']['draft'] = index['versions']['published']
        self.bulk.update_course_index(self.course_key, index_copy)
        self.bulk._end_bulk_operation(self.course_key)
        self.conn.upsert_structure.assert_called_once_with(published_structure)
        self.conn.update_course_index.assert_called_once_with(index_copy, from_index=self.conn.get_course_index.return_value)
        self.conn.get_course_index.assert_called_once_with(self.course_key)


class TestBulkWriteMixinOpenAfterPrevTransaction(TestBulkWriteMixinOpen, TestBulkWriteMixinPreviousTransaction):
    """
    Test that operations on with an open transaction aren't affected by a previously executed transaction
    """
    pass
