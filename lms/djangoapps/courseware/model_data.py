import json
from collections import namedtuple
from .models import (
    StudentModule,
    XModuleContentField,
    XModuleSettingsField,
    XModuleStudentPrefsField,
    XModuleStudentInfoField
)

from xmodule.runtime import DbModel, KeyValueStore
from xmodule.model import Scope


class InvalidScopeError(Exception):
    pass

class InvalidWriteError(Exception):
    pass


class LmsKeyValueStore(KeyValueStore):
    """
    This KeyValueStore will read data from descriptor_model_data if it exists,
    but will not overwrite any keys set in descriptor_model_data. Attempts to do so will
    raise an InvalidWriteError.

    If the scope to write to is not one of the 5 named scopes:
        Scope.content
        Scope.settings
        Scope.student_state
        Scope.student_preferences
        Scope.student_info
    then an InvalidScopeError will be raised.

    Data for Scope.student_state is stored as StudentModule objects via the django orm.

    Data for the other scopes is stored in individual objects that are named for the
    scope involved and have the field name as a key

    If the key isn't found in the expected table during a read or a delete, then a KeyError will be raised
    """
    def __init__(self, course_id, user, descriptor_model_data, student_module_cache):
        self._course_id = course_id
        self._user = user
        self._descriptor_model_data = descriptor_model_data
        self._student_module_cache = student_module_cache

    def _student_module(self, key):
        student_module = self._student_module_cache.lookup(
            self._course_id, key.module_scope_id.category, key.module_scope_id.url()
        )
        return student_module

    def _field_object(self, key):
        if key.scope == Scope.content:
            return XModuleContentField, {'field_name': key.field_name, 'definition_id': key.module_scope_id}
        elif key.scope == Scope.settings:
            return XModuleSettingsField, {
                'field_name': key.field_name,
                'usage_id': '%s-%s' % (self._course_id, key.module_scope_id)
            }
        elif key.scope == Scope.student_preferences:
            return XModuleStudentPrefsField, {'field_name': key.field_name, 'student': self._user, 'module_type': key.module_scope_id}
        elif key.scope == Scope.student_info:
            return XModuleStudentInfoField, {'field_name': key.field_name, 'student': self._user}

        raise InvalidScopeError(key.scope)

    def get(self, key):
        if key.field_name in self._descriptor_model_data:
            return self._descriptor_model_data[key.field_name]

        if key.scope == Scope.student_state:
            student_module = self._student_module(key)

            if student_module is None:
                raise KeyError(key.field_name)

            return json.loads(student_module.state)[key.field_name]

        scope_field_cls, search_kwargs = self._field_object(key)
        try:
            return json.loads(scope_field_cls.objects.get(**search_kwargs).value)
        except scope_field_cls.DoesNotExist:
            raise KeyError(key.field_name)

    def set(self, key, value):
        if key.field_name in self._descriptor_model_data:
            raise InvalidWriteError("Not allowed to overwrite descriptor model data", key.field_name)

        if key.scope == Scope.student_state:
            student_module = self._student_module(key)
            if student_module is None:
                student_module = StudentModule(
                    course_id=self._course_id,
                    student=self._user,
                    module_type=key.module_scope_id.category,
                    module_state_key=key.module_scope_id.url(),
                    state=json.dumps({})
                )
                self._student_module_cache.append(student_module)
            state = json.loads(student_module.state)
            state[key.field_name] = value
            student_module.state = json.dumps(state)
            student_module.save()
            return

        scope_field_cls, search_kwargs = self._field_object(key)
        json_value = json.dumps(value)
        field, created = scope_field_cls.objects.select_for_update().get_or_create(
            defaults={'value': json_value},
            **search_kwargs
        )
        if not created:
            field.value = json_value
            field.save()

    def delete(self, key):
        if key.field_name in self._descriptor_model_data:
            raise InvalidWriteError("Not allowed to deleted descriptor model data", key.field_name)

        if key.scope == Scope.student_state:
            student_module = self._student_module(key)

            if student_module is None:
                raise KeyError(key.field_name)

            state = json.loads(student_module.state)
            del state[key.field_name]
            student_module.state = json.dumps(state)
            student_module.save()
            return

        scope_field_cls, search_kwargs = self._field_object(key)
        print scope_field_cls, search_kwargs
        query = scope_field_cls.objects.filter(**search_kwargs)
        if not query.exists():
            raise KeyError(key.field_name)

        query.delete()


LmsUsage = namedtuple('LmsUsage', 'id, def_id')

