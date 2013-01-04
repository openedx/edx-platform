import factory
import json
from mock import Mock
from django.contrib.auth.models import User

from functools import partial

from courseware.model_data import LmsKeyValueStore, InvalidWriteError, InvalidScopeError
from courseware.models import StudentModule, XModuleContentField, XModuleSettingsField, XModuleStudentInfoField, XModuleStudentPrefsField, StudentModuleCache
from xblock.core import Scope, BlockScope
from xmodule.modulestore import Location

from django.test import TestCase


def mock_descriptor():
    descriptor = Mock()
    descriptor.stores_state = True
    descriptor.location = location('def_id')
    return descriptor

location = partial(Location, 'i4x', 'edX', 'test_course', 'problem')
course_id = 'edX/test_course/test'

content_key = partial(LmsKeyValueStore.Key, Scope.content, None, location('def_id'))
settings_key = partial(LmsKeyValueStore.Key, Scope.settings, None, location('def_id'))
student_state_key = partial(LmsKeyValueStore.Key, Scope.student_state, 'user', location('def_id'))
student_prefs_key = partial(LmsKeyValueStore.Key, Scope.student_preferences, 'user', 'problem')
student_info_key = partial(LmsKeyValueStore.Key, Scope.student_info, 'user', None)


class UserFactory(factory.Factory):
    FACTORY_FOR = User

    username = 'user'


class StudentModuleFactory(factory.Factory):
    FACTORY_FOR = StudentModule

    module_type = 'problem'
    module_state_key = location('def_id').url()
    student = factory.SubFactory(UserFactory)
    course_id = course_id
    state = None


class ContentFactory(factory.Factory):
    FACTORY_FOR = XModuleContentField

    field_name = 'content_field'
    value = json.dumps('content_value')
    definition_id = location('def_id').url()


class SettingsFactory(factory.Factory):
    FACTORY_FOR = XModuleSettingsField

    field_name = 'settings_field'
    value = json.dumps('settings_value')
    usage_id = '%s-%s' % (course_id, location('def_id').url())


class StudentPrefsFactory(factory.Factory):
    FACTORY_FOR = XModuleStudentPrefsField

    field_name = 'student_pref_field'
    value = json.dumps('student_pref_value')
    student = factory.SubFactory(UserFactory)
    module_type = 'problem'


class StudentInfoFactory(factory.Factory):
    FACTORY_FOR = XModuleStudentInfoField

    field_name = 'student_info_field'
    value = json.dumps('student_info_value')
    student = factory.SubFactory(UserFactory)


class TestDescriptorFallback(TestCase):

    def setUp(self):
        self.desc_md = {
            'field_a': 'content',
            'field_b': 'settings',
        }
        self.kvs = LmsKeyValueStore(course_id, UserFactory.build(), self.desc_md, None)

    def test_get_from_descriptor(self):
        self.assertEquals('content', self.kvs.get(content_key('field_a')))
        self.assertEquals('settings', self.kvs.get(settings_key('field_b')))

    def test_write_to_descriptor(self):
        self.assertRaises(InvalidWriteError, self.kvs.set, content_key('field_a'), 'foo')
        self.assertEquals('content', self.desc_md['field_a'])
        self.assertRaises(InvalidWriteError, self.kvs.set, settings_key('field_b'), 'foo')
        self.assertEquals('settings', self.desc_md['field_b'])

        self.assertRaises(InvalidWriteError, self.kvs.delete, content_key('field_a'))
        self.assertEquals('content', self.desc_md['field_a'])
        self.assertRaises(InvalidWriteError, self.kvs.delete, settings_key('field_b'))
        self.assertEquals('settings', self.desc_md['field_b'])


class TestStudentStateFields(TestCase):
    pass

class TestInvalidScopes(TestCase):
    def setUp(self):
        self.desc_md = {}
        self.kvs = LmsKeyValueStore(course_id, UserFactory.build(), self.desc_md, None)

    def test_invalid_scopes(self):
        for scope in (Scope(student=True, block=BlockScope.DEFINITION),
                      Scope(student=False, block=BlockScope.TYPE),
                      Scope(student=False, block=BlockScope.ALL)):
            self.assertRaises(InvalidScopeError, self.kvs.get, LmsKeyValueStore.Key(scope, None, None, 'field'))
            self.assertRaises(InvalidScopeError, self.kvs.set, LmsKeyValueStore.Key(scope, None, None, 'field'), 'value')
            self.assertRaises(InvalidScopeError, self.kvs.delete, LmsKeyValueStore.Key(scope, None, None, 'field'))


class TestStudentModuleStorage(TestCase):

    def setUp(self):
        student_module = StudentModuleFactory.create(state=json.dumps({'a_field': 'a_value'}))
        self.user = student_module.student
        self.desc_md = {}
        self.smc = StudentModuleCache(course_id, self.user, [mock_descriptor()])
        self.kvs = LmsKeyValueStore(course_id, self.user, self.desc_md, self.smc)


    def test_get_existing_field(self):
        "Test that getting an existing field in an existing StudentModule works"
        self.assertEquals('a_value', self.kvs.get(student_state_key('a_field')))

    def test_get_missing_field(self):
        "Test that getting a missing field from an existing StudentModule raises a KeyError"
        self.assertRaises(KeyError, self.kvs.get, student_state_key('not_a_field'))

    def test_set_existing_field(self):
        "Test that setting an existing student_state field changes the value"
        self.kvs.set(student_state_key('a_field'), 'new_value')
        self.assertEquals(1, StudentModule.objects.all().count())
        self.assertEquals({'a_field': 'new_value'}, json.loads(StudentModule.objects.all()[0].state))

    def test_set_missing_field(self):
        "Test that setting a new student_state field changes the value"
        self.kvs.set(student_state_key('not_a_field'), 'new_value')
        self.assertEquals(1, StudentModule.objects.all().count())
        self.assertEquals({'a_field': 'a_value', 'not_a_field': 'new_value'}, json.loads(StudentModule.objects.all()[0].state))

    def test_delete_existing_field(self):
        "Test that deleting an existing field removes it from the StudentModule"
        self.kvs.delete(student_state_key('a_field'))
        self.assertEquals(1, StudentModule.objects.all().count())
        self.assertEquals({}, json.loads(StudentModule.objects.all()[0].state))

    def test_delete_missing_field(self):
        "Test that deleting a missing field from an existing StudentModule raises a KeyError"
        self.assertRaises(KeyError, self.kvs.delete, student_state_key('not_a_field'))
        self.assertEquals(1, StudentModule.objects.all().count())
        self.assertEquals({'a_field': 'a_value'}, json.loads(StudentModule.objects.all()[0].state))


class TestMissingStudentModule(TestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.desc_md = {}
        self.smc = StudentModuleCache(course_id, self.user, [mock_descriptor()])
        self.kvs = LmsKeyValueStore(course_id, self.user, self.desc_md, self.smc)

    def test_get_field_from_missing_student_module(self):
        "Test that getting a field from a missing StudentModule raises a KeyError"
        self.assertRaises(KeyError, self.kvs.get, student_state_key('a_field'))

    def test_set_field_in_missing_student_module(self):
        "Test that setting a field in a missing StudentModule creates the student module"
        self.assertEquals(0, len(self.smc.cache))
        self.assertEquals(0, StudentModule.objects.all().count())

        self.kvs.set(student_state_key('a_field'), 'a_value')

        self.assertEquals(1, len(self.smc.cache))
        self.assertEquals(1, StudentModule.objects.all().count())

        student_module = StudentModule.objects.all()[0]
        self.assertEquals({'a_field': 'a_value'}, json.loads(student_module.state))
        self.assertEquals(self.user, student_module.student)
        self.assertEquals(location('def_id').url(), student_module.module_state_key)
        self.assertEquals(course_id, student_module.course_id)

    def test_delete_field_from_missing_student_module(self):
        "Test that deleting a field from a missing StudentModule raises a KeyError"
        self.assertRaises(KeyError, self.kvs.delete, student_state_key('a_field'))


class TestSettingsStorage(TestCase):

    def setUp(self):
        settings = SettingsFactory.create()
        self.user = UserFactory.create()
        self.desc_md = {}
        self.smc = StudentModuleCache(course_id, self.user, [])
        self.kvs = LmsKeyValueStore(course_id, self.user, self.desc_md, self.smc)

    def test_get_existing_field(self):
        "Test that getting an existing field in an existing SettingsField works"
        self.assertEquals('settings_value', self.kvs.get(settings_key('settings_field')))

    def test_get_missing_field(self):
        "Test that getting a missing field from an existing SettingsField raises a KeyError"
        self.assertRaises(KeyError, self.kvs.get, settings_key('not_settings_field'))

    def test_set_existing_field(self):
        "Test that setting an existing field changes the value"
        self.kvs.set(settings_key('settings_field'), 'new_value')
        self.assertEquals(1, XModuleSettingsField.objects.all().count())
        self.assertEquals('new_value', json.loads(XModuleSettingsField.objects.all()[0].value))

    def test_set_missing_field(self):
        "Test that setting a new field changes the value"
        self.kvs.set(settings_key('not_settings_field'), 'new_value')
        self.assertEquals(2, XModuleSettingsField.objects.all().count())
        self.assertEquals('settings_value', json.loads(XModuleSettingsField.objects.get(field_name='settings_field').value))
        self.assertEquals('new_value', json.loads(XModuleSettingsField.objects.get(field_name='not_settings_field').value))

    def test_delete_existing_field(self):
        "Test that deleting an existing field removes it"
        self.kvs.delete(settings_key('settings_field'))
        self.assertEquals(0, XModuleSettingsField.objects.all().count())

    def test_delete_missing_field(self):
        "Test that deleting a missing field from an existing SettingsField raises a KeyError"
        self.assertRaises(KeyError, self.kvs.delete, settings_key('not_settings_field'))
        self.assertEquals(1, XModuleSettingsField.objects.all().count())


class TestContentStorage(TestCase):

    def setUp(self):
        content = ContentFactory.create()
        self.user = UserFactory.create()
        self.desc_md = {}
        self.smc = StudentModuleCache(course_id, self.user, [])
        self.kvs = LmsKeyValueStore(course_id, self.user, self.desc_md, self.smc)

    def test_get_existing_field(self):
        "Test that getting an existing field in an existing ContentField works"
        self.assertEquals('content_value', self.kvs.get(content_key('content_field')))

    def test_get_missing_field(self):
        "Test that getting a missing field from an existing ContentField raises a KeyError"
        self.assertRaises(KeyError, self.kvs.get, content_key('not_content_field'))

    def test_set_existing_field(self):
        "Test that setting an existing field changes the value"
        self.kvs.set(content_key('content_field'), 'new_value')
        self.assertEquals(1, XModuleContentField.objects.all().count())
        self.assertEquals('new_value', json.loads(XModuleContentField.objects.all()[0].value))

    def test_set_missing_field(self):
        "Test that setting a new field changes the value"
        self.kvs.set(content_key('not_content_field'), 'new_value')
        self.assertEquals(2, XModuleContentField.objects.all().count())
        self.assertEquals('content_value', json.loads(XModuleContentField.objects.get(field_name='content_field').value))
        self.assertEquals('new_value', json.loads(XModuleContentField.objects.get(field_name='not_content_field').value))

    def test_delete_existing_field(self):
        "Test that deleting an existing field removes it"
        self.kvs.delete(content_key('content_field'))
        self.assertEquals(0, XModuleContentField.objects.all().count())

    def test_delete_missing_field(self):
        "Test that deleting a missing field from an existing ContentField raises a KeyError"
        self.assertRaises(KeyError, self.kvs.delete, content_key('not_content_field'))
        self.assertEquals(1, XModuleContentField.objects.all().count())


class TestStudentPrefsStorage(TestCase):

    def setUp(self):
        student_pref = StudentPrefsFactory.create()
        self.user = student_pref.student
        self.desc_md = {}
        self.smc = StudentModuleCache(course_id, self.user, [])
        self.kvs = LmsKeyValueStore(course_id, self.user, self.desc_md, self.smc)

    def test_get_existing_field(self):
        "Test that getting an existing field in an existing StudentPrefsField works"
        self.assertEquals('student_pref_value', self.kvs.get(student_prefs_key('student_pref_field')))

    def test_get_missing_field(self):
        "Test that getting a missing field from an existing StudentPrefsField raises a KeyError"
        self.assertRaises(KeyError, self.kvs.get, student_prefs_key('not_student_pref_field'))

    def test_set_existing_field(self):
        "Test that setting an existing field changes the value"
        self.kvs.set(student_prefs_key('student_pref_field'), 'new_value')
        self.assertEquals(1, XModuleStudentPrefsField.objects.all().count())
        self.assertEquals('new_value', json.loads(XModuleStudentPrefsField.objects.all()[0].value))

    def test_set_missing_field(self):
        "Test that setting a new field changes the value"
        self.kvs.set(student_prefs_key('not_student_pref_field'), 'new_value')
        self.assertEquals(2, XModuleStudentPrefsField.objects.all().count())
        self.assertEquals('student_pref_value', json.loads(XModuleStudentPrefsField.objects.get(field_name='student_pref_field').value))
        self.assertEquals('new_value', json.loads(XModuleStudentPrefsField.objects.get(field_name='not_student_pref_field').value))

    def test_delete_existing_field(self):
        "Test that deleting an existing field removes it"
        print list(XModuleStudentPrefsField.objects.all())
        self.kvs.delete(student_prefs_key('student_pref_field'))
        self.assertEquals(0, XModuleStudentPrefsField.objects.all().count())

    def test_delete_missing_field(self):
        "Test that deleting a missing field from an existing StudentPrefsField raises a KeyError"
        self.assertRaises(KeyError, self.kvs.delete, student_prefs_key('not_student_pref_field'))
        self.assertEquals(1, XModuleStudentPrefsField.objects.all().count())


class TestStudentInfoStorage(TestCase):

    def setUp(self):
        student_info = StudentInfoFactory.create()
        self.user = student_info.student
        self.desc_md = {}
        self.smc = StudentModuleCache(course_id, self.user, [])
        self.kvs = LmsKeyValueStore(course_id, self.user, self.desc_md, self.smc)

    def test_get_existing_field(self):
        "Test that getting an existing field in an existing StudentInfoField works"
        self.assertEquals('student_info_value', self.kvs.get(student_info_key('student_info_field')))

    def test_get_missing_field(self):
        "Test that getting a missing field from an existing StudentInfoField raises a KeyError"
        self.assertRaises(KeyError, self.kvs.get, student_info_key('not_student_info_field'))

    def test_set_existing_field(self):
        "Test that setting an existing field changes the value"
        self.kvs.set(student_info_key('student_info_field'), 'new_value')
        self.assertEquals(1, XModuleStudentInfoField.objects.all().count())
        self.assertEquals('new_value', json.loads(XModuleStudentInfoField.objects.all()[0].value))

    def test_set_missing_field(self):
        "Test that setting a new field changes the value"
        self.kvs.set(student_info_key('not_student_info_field'), 'new_value')
        self.assertEquals(2, XModuleStudentInfoField.objects.all().count())
        self.assertEquals('student_info_value', json.loads(XModuleStudentInfoField.objects.get(field_name='student_info_field').value))
        self.assertEquals('new_value', json.loads(XModuleStudentInfoField.objects.get(field_name='not_student_info_field').value))

    def test_delete_existing_field(self):
        "Test that deleting an existing field removes it"
        self.kvs.delete(student_info_key('student_info_field'))
        self.assertEquals(0, XModuleStudentInfoField.objects.all().count())

    def test_delete_missing_field(self):
        "Test that deleting a missing field from an existing StudentInfoField raises a KeyError"
        self.assertRaises(KeyError, self.kvs.delete, student_info_key('not_student_info_field'))
        self.assertEquals(1, XModuleStudentInfoField.objects.all().count())
