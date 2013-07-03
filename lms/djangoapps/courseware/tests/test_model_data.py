"""
Test for lms courseware app, module data (runtime data storage for XBlocks)
"""
import json
from mock import Mock, patch
from functools import partial

from courseware.model_data import LmsKeyValueStore, InvalidWriteError
from courseware.model_data import InvalidScopeError, ModelDataCache
from courseware.models import StudentModule, XModuleContentField, XModuleSettingsField
from courseware.models import XModuleStudentInfoField, XModuleStudentPrefsField

from student.tests.factories import UserFactory
from courseware.tests.factories import StudentModuleFactory as cmfStudentModuleFactory
from courseware.tests.factories import ContentFactory, SettingsFactory
from courseware.tests.factories import StudentPrefsFactory, StudentInfoFactory

from xblock.core import Scope, BlockScope
from xmodule.modulestore import Location
from django.test import TestCase
from django.db import DatabaseError
from xblock.core import KeyValueMultiSaveError


def mock_field(scope, name):
    field = Mock()
    field.scope = scope
    field.name = name
    return field


def mock_descriptor(fields=[], lms_fields=[]):
    descriptor = Mock()
    descriptor.location = location('def_id')
    descriptor.module_class.fields = fields
    descriptor.module_class.lms.fields = lms_fields
    descriptor.module_class.__name__ = 'MockProblemModule'
    return descriptor

location = partial(Location, 'i4x', 'edX', 'test_course', 'problem')
course_id = 'edX/test_course/test'

content_key = partial(LmsKeyValueStore.Key, Scope.content, None, location('def_id'))
settings_key = partial(LmsKeyValueStore.Key, Scope.settings, None, location('def_id'))
user_state_key = partial(LmsKeyValueStore.Key, Scope.user_state, 'user', location('def_id'))
prefs_key = partial(LmsKeyValueStore.Key, Scope.preferences, 'user', 'MockProblemModule')
user_info_key = partial(LmsKeyValueStore.Key, Scope.user_info, 'user', None)


class StudentModuleFactory(cmfStudentModuleFactory):
    module_state_key = location('def_id').url()
    course_id = course_id


class TestDescriptorFallback(TestCase):

    def setUp(self):
        self.desc_md = {
            'field_a': 'content',
            'field_b': 'settings',
        }
        self.kvs = LmsKeyValueStore(self.desc_md, None)

    def test_get_from_descriptor(self):
        self.assertEquals('content', self.kvs.get(content_key('field_a')))
        self.assertEquals('settings', self.kvs.get(settings_key('field_b')))

    def test_write_to_descriptor(self):
        self.assertRaises(InvalidWriteError, self.kvs.set, content_key('field_a'), 'foo')
        self.assertEquals('content', self.desc_md['field_a'])
        self.assertRaises(InvalidWriteError, self.kvs.set, settings_key('field_b'), 'foo')
        self.assertEquals('settings', self.desc_md['field_b'])

        self.assertRaises(InvalidWriteError, self.kvs.set_many, {content_key('field_a'): 'foo'})
        self.assertEquals('content', self.desc_md['field_a'])

        self.assertRaises(InvalidWriteError, self.kvs.delete, content_key('field_a'))
        self.assertEquals('content', self.desc_md['field_a'])
        self.assertRaises(InvalidWriteError, self.kvs.delete, settings_key('field_b'))
        self.assertEquals('settings', self.desc_md['field_b'])




class TestInvalidScopes(TestCase):
    def setUp(self):
        self.desc_md = {}
        self.user = UserFactory.create(username='user')
        self.mdc = ModelDataCache([mock_descriptor([mock_field(Scope.user_state, 'a_field')])], course_id, self.user)
        self.kvs = LmsKeyValueStore(self.desc_md, self.mdc)

    def test_invalid_scopes(self):
        for scope in (Scope(user=True, block=BlockScope.DEFINITION),
                      Scope(user=False, block=BlockScope.TYPE),
                      Scope(user=False, block=BlockScope.ALL)):
            key = LmsKeyValueStore.Key(scope, None, None, 'field')

            self.assertRaises(InvalidScopeError, self.kvs.get, key)
            self.assertRaises(InvalidScopeError, self.kvs.set, key, 'value')
            self.assertRaises(InvalidScopeError, self.kvs.delete, key)
            self.assertRaises(InvalidScopeError, self.kvs.has, key)
            self.assertRaises(InvalidScopeError, self.kvs.set_many, {key: 'value'})


class TestStudentModuleStorage(TestCase):

    def setUp(self):
        self.desc_md = {}
        student_module = StudentModuleFactory(state=json.dumps({'a_field': 'a_value', 'b_field': 'b_value'}))
        self.user = student_module.student
        self.mdc = ModelDataCache([mock_descriptor([mock_field(Scope.user_state, 'a_field')])], course_id, self.user)
        self.kvs = LmsKeyValueStore(self.desc_md, self.mdc)

    def test_get_existing_field(self):
        "Test that getting an existing field in an existing StudentModule works"
        self.assertEquals('a_value', self.kvs.get(user_state_key('a_field')))

    def test_get_missing_field(self):
        "Test that getting a missing field from an existing StudentModule raises a KeyError"
        self.assertRaises(KeyError, self.kvs.get, user_state_key('not_a_field'))

    def test_set_existing_field(self):
        "Test that setting an existing user_state field changes the value"
        self.kvs.set(user_state_key('a_field'), 'new_value')
        self.assertEquals(1, StudentModule.objects.all().count())
        self.assertEquals({'b_field': 'b_value', 'a_field': 'new_value'}, json.loads(StudentModule.objects.all()[0].state))

    def test_set_missing_field(self):
        "Test that setting a new user_state field changes the value"
        self.kvs.set(user_state_key('not_a_field'), 'new_value')
        self.assertEquals(1, StudentModule.objects.all().count())
        self.assertEquals({'b_field': 'b_value', 'a_field': 'a_value', 'not_a_field': 'new_value'}, json.loads(StudentModule.objects.all()[0].state))

    def test_delete_existing_field(self):
        "Test that deleting an existing field removes it from the StudentModule"
        self.kvs.delete(user_state_key('a_field'))
        self.assertEquals(1, StudentModule.objects.all().count())
        self.assertRaises(KeyError, self.kvs.get, user_state_key('not_a_field'))

    def test_delete_missing_field(self):
        "Test that deleting a missing field from an existing StudentModule raises a KeyError"
        self.assertRaises(KeyError, self.kvs.delete, user_state_key('not_a_field'))
        self.assertEquals(1, StudentModule.objects.all().count())
        self.assertEquals({'b_field': 'b_value', 'a_field': 'a_value'}, json.loads(StudentModule.objects.all()[0].state))

    def test_has_existing_field(self):
        "Test that `has` returns True for existing fields in StudentModules"
        self.assertTrue(self.kvs.has(user_state_key('a_field')))

    def test_has_missing_field(self):
        "Test that `has` returns False for missing fields in StudentModule"
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
        self.assertEquals(len(exception_context.exception.saved_field_names), 0)


class TestMissingStudentModule(TestCase):
    def setUp(self):
        self.user = UserFactory.create(username='user')
        self.desc_md = {}
        self.mdc = ModelDataCache([mock_descriptor()], course_id, self.user)
        self.kvs = LmsKeyValueStore(self.desc_md, self.mdc)

    def test_get_field_from_missing_student_module(self):
        "Test that getting a field from a missing StudentModule raises a KeyError"
        self.assertRaises(KeyError, self.kvs.get, user_state_key('a_field'))

    def test_set_field_in_missing_student_module(self):
        "Test that setting a field in a missing StudentModule creates the student module"
        self.assertEquals(0, len(self.mdc.cache))
        self.assertEquals(0, StudentModule.objects.all().count())

        self.kvs.set(user_state_key('a_field'), 'a_value')

        self.assertEquals(1, len(self.mdc.cache))
        self.assertEquals(1, StudentModule.objects.all().count())

        student_module = StudentModule.objects.all()[0]
        self.assertEquals({'a_field': 'a_value'}, json.loads(student_module.state))
        self.assertEquals(self.user, student_module.student)
        self.assertEquals(location('def_id').url(), student_module.module_state_key)
        self.assertEquals(course_id, student_module.course_id)

    def test_delete_field_from_missing_student_module(self):
        "Test that deleting a field from a missing StudentModule raises a KeyError"
        self.assertRaises(KeyError, self.kvs.delete, user_state_key('a_field'))

    def test_has_field_for_missing_student_module(self):
        "Test that `has` returns False for missing StudentModules"
        self.assertFalse(self.kvs.has(user_state_key('a_field')))


class StorageTestBase(object):
    """
    A base class for that gets subclassed when testing each of the scopes.

    """
    # Disable pylint warnings that arise because of the way the child classes call
    # this base class -- pylint's static analysis can't keep up with it.
    # pylint: disable=E1101, E1102

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
        self.desc_md = {}
        self.mock_descriptor = mock_descriptor([
            mock_field(self.scope, 'existing_field'),
            mock_field(self.scope, 'other_existing_field')])
        self.mdc = ModelDataCache([self.mock_descriptor], course_id, self.user)
        self.kvs = LmsKeyValueStore(self.desc_md, self.mdc)

    def test_set_and_get_existing_field(self):
        self.kvs.set(self.key_factory('existing_field'), 'test_value')
        self.assertEquals('test_value', self.kvs.get(self.key_factory('existing_field')))

    def test_get_existing_field(self):
        "Test that getting an existing field in an existing Storage Field works"
        self.assertEquals('old_value', self.kvs.get(self.key_factory('existing_field')))

    def test_get_missing_field(self):
        "Test that getting a missing field from an existing Storage Field raises a KeyError"
        self.assertRaises(KeyError, self.kvs.get, self.key_factory('missing_field'))

    def test_set_existing_field(self):
        "Test that setting an existing field changes the value"
        self.kvs.set(self.key_factory('existing_field'), 'new_value')
        self.assertEquals(1, self.storage_class.objects.all().count())
        self.assertEquals('new_value', json.loads(self.storage_class.objects.all()[0].value))

    def test_set_missing_field(self):
        "Test that setting a new field changes the value"
        self.kvs.set(self.key_factory('missing_field'), 'new_value')
        self.assertEquals(2, self.storage_class.objects.all().count())
        self.assertEquals('old_value', json.loads(self.storage_class.objects.get(field_name='existing_field').value))
        self.assertEquals('new_value', json.loads(self.storage_class.objects.get(field_name='missing_field').value))

    def test_delete_existing_field(self):
        "Test that deleting an existing field removes it"
        self.kvs.delete(self.key_factory('existing_field'))
        self.assertEquals(0, self.storage_class.objects.all().count())

    def test_delete_missing_field(self):
        "Test that deleting a missing field from an existing Storage Field raises a KeyError"
        self.assertRaises(KeyError, self.kvs.delete, self.key_factory('missing_field'))
        self.assertEquals(1, self.storage_class.objects.all().count())

    def test_has_existing_field(self):
        "Test that `has` returns True for an existing Storage Field"
        self.assertTrue(self.kvs.has(self.key_factory('existing_field')))

    def test_has_missing_field(self):
        "Test that `has` return False for an existing Storage Field"
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

        self.kvs.set_many(kv_dict)
        for key in kv_dict:
            self.assertEquals(self.kvs.get(key), kv_dict[key])

    def test_set_many_failure(self):
        """Test that setting many regular fields with a DB error """
        kv_dict = self.construct_kv_dict()
        for key in kv_dict:
            self.kvs.set(key, 'test value')

        with patch('django.db.models.Model.save', side_effect=[None, DatabaseError]):
            with self.assertRaises(KeyValueMultiSaveError) as exception_context:
                self.kvs.set_many(kv_dict)

        exception = exception_context.exception
        self.assertEquals(len(exception.saved_field_names), 1)
        self.assertEquals(exception.saved_field_names[0], 'existing_field')




class TestSettingsStorage(StorageTestBase, TestCase):
    factory = SettingsFactory
    scope = Scope.settings
    key_factory = settings_key
    storage_class = XModuleSettingsField


class TestContentStorage(StorageTestBase, TestCase):
    factory = ContentFactory
    scope = Scope.content
    key_factory = content_key
    storage_class = XModuleContentField


class TestStudentPrefsStorage(StorageTestBase, TestCase):
    factory = StudentPrefsFactory
    scope = Scope.preferences
    key_factory = prefs_key
    storage_class = XModuleStudentPrefsField


class TestStudentInfoStorage(StorageTestBase, TestCase):
    factory = StudentInfoFactory
    scope = Scope.user_info
    key_factory = user_info_key
    storage_class = XModuleStudentInfoField
