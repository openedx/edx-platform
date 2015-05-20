"""
Test for lms courseware app, module data (runtime data storage for XBlocks)
"""
import json
from mock import Mock, patch
from nose.plugins.attrib import attr
from functools import partial

from courseware.model_data import DjangoKeyValueStore
from courseware.model_data import InvalidScopeError, FieldDataCache
from courseware.models import StudentModule
from courseware.models import XModuleStudentInfoField, XModuleStudentPrefsField

from student.tests.factories import UserFactory
from courseware.tests.factories import StudentModuleFactory as cmfStudentModuleFactory, location, course_id
from courseware.tests.factories import UserStateSummaryFactory
from courseware.tests.factories import StudentPrefsFactory, StudentInfoFactory

from xblock.fields import Scope, BlockScope, ScopeIds
from xblock.exceptions import KeyValueMultiSaveError
from xblock.core import XBlock
from django.test import TestCase
from django.db import DatabaseError


def mock_field(scope, name):
    field = Mock()
    field.scope = scope
    field.name = name
    return field


def mock_descriptor(fields=[]):
    descriptor = Mock(entry_point=XBlock.entry_point)
    descriptor.scope_ids = ScopeIds('user1', 'mock_problem', location('def_id'), location('usage_id'))
    descriptor.module_class.fields.values.return_value = fields
    descriptor.fields.values.return_value = fields
    descriptor.module_class.__name__ = 'MockProblemModule'
    return descriptor

# The user ids here are 1 because we make a student in the setUp functions, and
# they get an id of 1.  There's an assertion in setUp to ensure that assumption
# is still true.
user_state_summary_key = partial(DjangoKeyValueStore.Key, Scope.user_state_summary, None, location('usage_id'))
settings_key = partial(DjangoKeyValueStore.Key, Scope.settings, None, location('usage_id'))
user_state_key = partial(DjangoKeyValueStore.Key, Scope.user_state, 1, location('usage_id'))
prefs_key = partial(DjangoKeyValueStore.Key, Scope.preferences, 1, 'mock_problem')
user_info_key = partial(DjangoKeyValueStore.Key, Scope.user_info, 1, None)


class StudentModuleFactory(cmfStudentModuleFactory):
    module_state_key = location('usage_id')
    course_id = course_id


@attr('shard_1')
class TestInvalidScopes(TestCase):
    def setUp(self):
        super(TestInvalidScopes, self).setUp()
        self.user = UserFactory.create(username='user')
        self.field_data_cache = FieldDataCache([mock_descriptor([mock_field(Scope.user_state, 'a_field')])], course_id, self.user)
        self.kvs = DjangoKeyValueStore(self.field_data_cache)

    def test_invalid_scopes(self):
        for scope in (Scope(user=True, block=BlockScope.DEFINITION),
                      Scope(user=False, block=BlockScope.TYPE),
                      Scope(user=False, block=BlockScope.ALL)):
            key = DjangoKeyValueStore.Key(scope, None, None, 'field')

            self.assertRaises(InvalidScopeError, self.kvs.get, key)
            self.assertRaises(InvalidScopeError, self.kvs.set, key, 'value')
            self.assertRaises(InvalidScopeError, self.kvs.delete, key)
            self.assertRaises(InvalidScopeError, self.kvs.has, key)
            self.assertRaises(InvalidScopeError, self.kvs.set_many, {key: 'value'})


@attr('shard_1')
class OtherUserFailureTestMixin(object):
    """
    Mixin class to add test cases for failures when a user trying to use the kvs is not
    the one that instantiated the kvs.
    Doing a mixin rather than modifying StorageTestBase (below) because some scopes don't fail in this case, because
    they aren't bound to a particular user

    assumes that this is mixed into a class that defines other_key_factory and existing_field_name
    """
    def test_other_user_kvs_get_failure(self):
        """
        Test for assert failure when a user who didn't create the kvs tries to get from it it
        """
        with self.assertRaises(AssertionError):
            self.kvs.get(self.other_key_factory(self.existing_field_name))

    def test_other_user_kvs_set_failure(self):
        """
        Test for assert failure when a user who didn't create the kvs tries to get from it it
        """
        with self.assertRaises(AssertionError):
            self.kvs.set(self.other_key_factory(self.existing_field_name), "new_value")


@attr('shard_1')
class TestStudentModuleStorage(OtherUserFailureTestMixin, TestCase):
    """Tests for user_state storage via StudentModule"""
    other_key_factory = partial(DjangoKeyValueStore.Key, Scope.user_state, 2, location('usage_id'))  # user_id=2, not 1
    existing_field_name = "a_field"

    def setUp(self):
        super(TestStudentModuleStorage, self).setUp()
        student_module = StudentModuleFactory(state=json.dumps({'a_field': 'a_value', 'b_field': 'b_value'}))
        self.user = student_module.student
        self.assertEqual(self.user.id, 1)   # check our assumption hard-coded in the key functions above.

        # There should be only one query to load a single descriptor with a single user_state field
        with self.assertNumQueries(1):
            self.field_data_cache = FieldDataCache(
                [mock_descriptor([mock_field(Scope.user_state, 'a_field')])], course_id, self.user
            )

        self.kvs = DjangoKeyValueStore(self.field_data_cache)

    def test_get_existing_field(self):
        "Test that getting an existing field in an existing StudentModule works"
        # This should only read from the cache, not the database
        with self.assertNumQueries(0):
            self.assertEquals('a_value', self.kvs.get(user_state_key('a_field')))

    def test_get_missing_field(self):
        "Test that getting a missing field from an existing StudentModule raises a KeyError"
        # This should only read from the cache, not the database
        with self.assertNumQueries(0):
            self.assertRaises(KeyError, self.kvs.get, user_state_key('not_a_field'))

    def test_set_existing_field(self):
        "Test that setting an existing user_state field changes the value"
        # We are updating a problem, so we write to courseware_studentmodulehistory
        # as well as courseware_studentmodule. We also need to read the database
        # to discover if something other than the DjangoXBlockUserStateClient
        # has written to the StudentModule (such as UserStateCache setting the score
        # on the StudentModule).
        with self.assertNumQueries(3):
            self.kvs.set(user_state_key('a_field'), 'new_value')
        self.assertEquals(1, StudentModule.objects.all().count())
        self.assertEquals({'b_field': 'b_value', 'a_field': 'new_value'}, json.loads(StudentModule.objects.all()[0].state))

    def test_set_missing_field(self):
        "Test that setting a new user_state field changes the value"
        # We are updating a problem, so we write to courseware_studentmodulehistory
        # as well as courseware_studentmodule. We also need to read the database
        # to discover if something other than the DjangoXBlockUserStateClient
        # has written to the StudentModule (such as UserStateCache setting the score
        # on the StudentModule).
        with self.assertNumQueries(3):
            self.kvs.set(user_state_key('not_a_field'), 'new_value')
        self.assertEquals(1, StudentModule.objects.all().count())
        self.assertEquals({'b_field': 'b_value', 'a_field': 'a_value', 'not_a_field': 'new_value'}, json.loads(StudentModule.objects.all()[0].state))

    def test_delete_existing_field(self):
        "Test that deleting an existing field removes it from the StudentModule"
        # We are updating a problem, so we write to courseware_studentmodulehistory
        # as well as courseware_studentmodule. We also need to read the database
        # to discover if something other than the DjangoXBlockUserStateClient
        # has written to the StudentModule (such as UserStateCache setting the score
        # on the StudentModule).
        with self.assertNumQueries(3):
            self.kvs.delete(user_state_key('a_field'))
        self.assertEquals(1, StudentModule.objects.all().count())
        self.assertRaises(KeyError, self.kvs.get, user_state_key('not_a_field'))

    def test_delete_missing_field(self):
        "Test that deleting a missing field from an existing StudentModule raises a KeyError"
        with self.assertNumQueries(0):
            self.assertRaises(KeyError, self.kvs.delete, user_state_key('not_a_field'))
        self.assertEquals(1, StudentModule.objects.all().count())
        self.assertEquals({'b_field': 'b_value', 'a_field': 'a_value'}, json.loads(StudentModule.objects.all()[0].state))

    def test_has_existing_field(self):
        "Test that `has` returns True for existing fields in StudentModules"
        with self.assertNumQueries(0):
            self.assertTrue(self.kvs.has(user_state_key('a_field')))

    def test_has_missing_field(self):
        "Test that `has` returns False for missing fields in StudentModule"
        with self.assertNumQueries(0):
            self.assertFalse(self.kvs.has(user_state_key('not_a_field')))

    def construct_kv_dict(self):
        """Construct a kv_dict that can be passed to set_many"""
        key1 = user_state_key('field_a')
        key2 = user_state_key('field_b')
        new_value = 'new value'
        newer_value = 'newer value'
        return {key1: new_value, key2: newer_value}

    def test_set_many(self):
        "Test setting many fields that are scoped to Scope.user_state"
        kv_dict = self.construct_kv_dict()

        # Scope.user_state is stored in a single row in the database, so we only
        # need to send a single update to that table.
        # We also are updating a problem, so we write to courseware student module history
        # We also need to read the database to discover if something other than the
        # DjangoXBlockUserStateClient has written to the StudentModule (such as
        # UserStateCache setting the score on the StudentModule).
        with self.assertNumQueries(3):
            self.kvs.set_many(kv_dict)

        for key in kv_dict:
            self.assertEquals(self.kvs.get(key), kv_dict[key])

    def test_set_many_failure(self):
        "Test failures when setting many fields that are scoped to Scope.user_state"
        kv_dict = self.construct_kv_dict()
        # because we're patching the underlying save, we need to ensure the
        # fields are in the cache
        for key in kv_dict:
            self.kvs.set(key, 'test_value')

        with patch('django.db.models.Model.save', side_effect=DatabaseError):
            with self.assertRaises(KeyValueMultiSaveError) as exception_context:
                self.kvs.set_many(kv_dict)
        self.assertEquals(exception_context.exception.saved_field_names, [])


@attr('shard_1')
class TestMissingStudentModule(TestCase):
    def setUp(self):
        super(TestMissingStudentModule, self).setUp()

        self.user = UserFactory.create(username='user')
        self.assertEqual(self.user.id, 1)   # check our assumption hard-coded in the key functions above.

        # The descriptor has no fields, so FDC shouldn't send any queries
        with self.assertNumQueries(0):
            self.field_data_cache = FieldDataCache([mock_descriptor()], course_id, self.user)
        self.kvs = DjangoKeyValueStore(self.field_data_cache)

    def test_get_field_from_missing_student_module(self):
        "Test that getting a field from a missing StudentModule raises a KeyError"
        with self.assertNumQueries(0):
            self.assertRaises(KeyError, self.kvs.get, user_state_key('a_field'))

    def test_set_field_in_missing_student_module(self):
        "Test that setting a field in a missing StudentModule creates the student module"
        self.assertEquals(0, len(self.field_data_cache))
        self.assertEquals(0, StudentModule.objects.all().count())

        # We are updating a problem, so we write to courseware_studentmodulehistory
        # as well as courseware_studentmodule. We also need to read the database
        # to discover if something other than the DjangoXBlockUserStateClient
        # has written to the StudentModule (such as UserStateCache setting the score
        # on the StudentModule).
        with self.assertNumQueries(3):
            self.kvs.set(user_state_key('a_field'), 'a_value')

        self.assertEquals(1, sum(len(cache) for cache in self.field_data_cache.cache.values()))
        self.assertEquals(1, StudentModule.objects.all().count())

        student_module = StudentModule.objects.all()[0]
        self.assertEquals({'a_field': 'a_value'}, json.loads(student_module.state))
        self.assertEquals(self.user, student_module.student)
        self.assertEquals(location('usage_id').replace(run=None), student_module.module_state_key)
        self.assertEquals(course_id, student_module.course_id)

    def test_delete_field_from_missing_student_module(self):
        "Test that deleting a field from a missing StudentModule raises a KeyError"
        with self.assertNumQueries(0):
            self.assertRaises(KeyError, self.kvs.delete, user_state_key('a_field'))

    def test_has_field_for_missing_student_module(self):
        "Test that `has` returns False for missing StudentModules"
        with self.assertNumQueries(0):
            self.assertFalse(self.kvs.has(user_state_key('a_field')))


@attr('shard_1')
class StorageTestBase(object):
    """
    A base class for that gets subclassed when testing each of the scopes.

    """
    # Disable pylint warnings that arise because of the way the child classes call
    # this base class -- pylint's static analysis can't keep up with it.
    # pylint: disable=no-member, not-callable

    factory = None
    scope = None
    key_factory = None
    storage_class = None

    def setUp(self):
        field_storage = self.factory.create()
        if hasattr(field_storage, 'student'):
            self.user = field_storage.student
        else:
            self.user = UserFactory.create()
        self.mock_descriptor = mock_descriptor([
            mock_field(self.scope, 'existing_field'),
            mock_field(self.scope, 'other_existing_field')])
        # Each field is stored as a separate row in the table,
        # but we can query them in a single query
        with self.assertNumQueries(1):
            self.field_data_cache = FieldDataCache([self.mock_descriptor], course_id, self.user)
        self.kvs = DjangoKeyValueStore(self.field_data_cache)

    def test_set_and_get_existing_field(self):
        with self.assertNumQueries(1):
            self.kvs.set(self.key_factory('existing_field'), 'test_value')
        with self.assertNumQueries(0):
            self.assertEquals('test_value', self.kvs.get(self.key_factory('existing_field')))

    def test_get_existing_field(self):
        "Test that getting an existing field in an existing Storage Field works"
        with self.assertNumQueries(0):
            self.assertEquals('old_value', self.kvs.get(self.key_factory('existing_field')))

    def test_get_missing_field(self):
        "Test that getting a missing field from an existing Storage Field raises a KeyError"
        with self.assertNumQueries(0):
            self.assertRaises(KeyError, self.kvs.get, self.key_factory('missing_field'))

    def test_set_existing_field(self):
        "Test that setting an existing field changes the value"
        with self.assertNumQueries(1):
            self.kvs.set(self.key_factory('existing_field'), 'new_value')
        self.assertEquals(1, self.storage_class.objects.all().count())
        self.assertEquals('new_value', json.loads(self.storage_class.objects.all()[0].value))

    def test_set_missing_field(self):
        "Test that setting a new field changes the value"
        with self.assertNumQueries(1):
            self.kvs.set(self.key_factory('missing_field'), 'new_value')
        self.assertEquals(2, self.storage_class.objects.all().count())
        self.assertEquals('old_value', json.loads(self.storage_class.objects.get(field_name='existing_field').value))
        self.assertEquals('new_value', json.loads(self.storage_class.objects.get(field_name='missing_field').value))

    def test_delete_existing_field(self):
        "Test that deleting an existing field removes it"
        with self.assertNumQueries(1):
            self.kvs.delete(self.key_factory('existing_field'))
        self.assertEquals(0, self.storage_class.objects.all().count())

    def test_delete_missing_field(self):
        "Test that deleting a missing field from an existing Storage Field raises a KeyError"
        with self.assertNumQueries(0):
            self.assertRaises(KeyError, self.kvs.delete, self.key_factory('missing_field'))
        self.assertEquals(1, self.storage_class.objects.all().count())

    def test_has_existing_field(self):
        "Test that `has` returns True for an existing Storage Field"
        with self.assertNumQueries(0):
            self.assertTrue(self.kvs.has(self.key_factory('existing_field')))

    def test_has_missing_field(self):
        "Test that `has` return False for an existing Storage Field"
        with self.assertNumQueries(0):
            self.assertFalse(self.kvs.has(self.key_factory('missing_field')))

    def construct_kv_dict(self):
        """Construct a kv_dict that can be passed to set_many"""
        key1 = self.key_factory('existing_field')
        key2 = self.key_factory('other_existing_field')
        new_value = 'new value'
        newer_value = 'newer value'
        return {key1: new_value, key2: newer_value}

    def test_set_many(self):
        """Test that setting many regular fields at the same time works"""
        kv_dict = self.construct_kv_dict()

        # Each field is a separate row in the database, hence
        # a separate query
        with self.assertNumQueries(len(kv_dict)):
            self.kvs.set_many(kv_dict)
        for key in kv_dict:
            self.assertEquals(self.kvs.get(key), kv_dict[key])

    def test_set_many_failure(self):
        """Test that setting many regular fields with a DB error """
        kv_dict = self.construct_kv_dict()
        for key in kv_dict:
            with self.assertNumQueries(1):
                self.kvs.set(key, 'test value')

        with patch('django.db.models.Model.save', side_effect=[None, DatabaseError]):
            with self.assertRaises(KeyValueMultiSaveError) as exception_context:
                self.kvs.set_many(kv_dict)

        exception = exception_context.exception
        self.assertEquals(exception.saved_field_names, ['existing_field', 'other_existing_field'])


class TestUserStateSummaryStorage(StorageTestBase, TestCase):
    """Tests for UserStateSummaryStorage"""
    factory = UserStateSummaryFactory
    scope = Scope.user_state_summary
    key_factory = user_state_summary_key
    storage_class = factory.FACTORY_FOR


class TestStudentPrefsStorage(OtherUserFailureTestMixin, StorageTestBase, TestCase):
    """Tests for StudentPrefStorage"""
    factory = StudentPrefsFactory
    scope = Scope.preferences
    key_factory = prefs_key
    storage_class = XModuleStudentPrefsField
    other_key_factory = partial(DjangoKeyValueStore.Key, Scope.preferences, 2, 'mock_problem')  # user_id=2, not 1
    existing_field_name = "existing_field"


class TestStudentInfoStorage(OtherUserFailureTestMixin, StorageTestBase, TestCase):
    """Tests for StudentInfoStorage"""
    factory = StudentInfoFactory
    scope = Scope.user_info
    key_factory = user_info_key
    storage_class = XModuleStudentInfoField
    other_key_factory = partial(DjangoKeyValueStore.Key, Scope.user_info, 2, 'mock_problem')  # user_id=2, not 1
    existing_field_name = "existing_field"
