"""
Classes to provide the LMS runtime data storage to XBlocks
"""

import json
from collections import namedtuple, defaultdict
from itertools import chain
from .models import (
    StudentModule,
    XModuleContentField,
    XModuleSettingsField,
    XModuleStudentPrefsField,
    XModuleStudentInfoField
)

from xblock.runtime import KeyValueStore, InvalidScopeError
from xblock.core import Scope


class InvalidWriteError(Exception):
    """
    Raised to indicate that writing to a particular key
    in the KeyValueStore is disabled
    """


def chunks(items, chunk_size):
    """
    Yields the values from items in chunks of size chunk_size
    """
    items = list(items)
    return (items[i:i + chunk_size] for i in xrange(0, len(items), chunk_size))


class ModelDataCache(object):
    """
    A cache of django model objects needed to supply the data
    for a module and its decendants
    """
    def __init__(self, descriptors, course_id, user, select_for_update=False):
        '''
        Find any courseware.models objects that are needed by any descriptor
        in descriptors. Attempts to minimize the number of queries to the database.
        Note: Only modules that have store_state = True or have shared
        state will have a StudentModule.

        Arguments
        descriptors: A list of XModuleDescriptors.
        course_id: The id of the current course
        user: The user for which to cache data
        select_for_update: True if rows should be locked until end of transaction
        '''
        self.cache = {}
        self.descriptors = descriptors
        self.select_for_update = select_for_update
        self.course_id = course_id
        self.user = user

        if user.is_authenticated():
            for scope, fields in self._fields_to_cache().items():
                for field_object in self._retrieve_fields(scope, fields):
                    self.cache[self._cache_key_from_field_object(scope, field_object)] = field_object

    @classmethod
    def cache_for_descriptor_descendents(cls, course_id, user, descriptor, depth=None,
                                         descriptor_filter=lambda descriptor: True,
                                         select_for_update=False):
        """
        course_id: the course in the context of which we want StudentModules.
        user: the django user for whom to load modules.
        descriptor: An XModuleDescriptor
        depth is the number of levels of descendent modules to load StudentModules for, in addition to
            the supplied descriptor. If depth is None, load all descendent StudentModules
        descriptor_filter is a function that accepts a descriptor and return wether the StudentModule
            should be cached
        select_for_update: Flag indicating whether the rows should be locked until end of transaction
        """

        def get_child_descriptors(descriptor, depth, descriptor_filter):
            """
            Return a list of all child descriptors down to the specified depth
            that match the descriptor filter. Includes `descriptor`

            descriptor: The parent to search inside
            depth: The number of levels to descend, or None for infinite depth
            descriptor_filter(descriptor): A function that returns True
                if descriptor should be included in the results
            """
            if descriptor_filter(descriptor):
                descriptors = [descriptor]
            else:
                descriptors = []

            if depth is None or depth > 0:
                new_depth = depth - 1 if depth is not None else depth

                for child in descriptor.get_children() + descriptor.get_required_module_descriptors():
                    descriptors.extend(get_child_descriptors(child, new_depth, descriptor_filter))

            return descriptors

        descriptors = get_child_descriptors(descriptor, depth, descriptor_filter)

        return ModelDataCache(descriptors, course_id, user, select_for_update)

    def _query(self, model_class, **kwargs):
        """
        Queries model_class with **kwargs, optionally adding select_for_update if
        self.select_for_update is set
        """
        query = model_class.objects
        if self.select_for_update:
            query = query.select_for_update()
        query = query.filter(**kwargs)
        return query

    def _chunked_query(self, model_class, chunk_field, items, chunk_size=500, **kwargs):
        """
        Queries model_class with `chunk_field` set to chunks of size `chunk_size`,
        and all other parameters from `**kwargs`

        This works around a limitation in sqlite3 on the number of parameters
        that can be put into a single query
        """
        res = chain.from_iterable(
            self._query(model_class, **dict([(chunk_field, chunk)] + kwargs.items()))
            for chunk in chunks(items, chunk_size)
        )
        return res

    def _retrieve_fields(self, scope, fields):
        """
        Queries the database for all of the fields in the specified scope
        """
        if scope in (Scope.children, Scope.parent):
            return []
        elif scope == Scope.user_state:
            return self._chunked_query(
                StudentModule,
                'module_state_key__in',
                (descriptor.location.url() for descriptor in self.descriptors),
                course_id=self.course_id,
                student=self.user.pk,
            )
        elif scope == Scope.content:
            return self._chunked_query(
                XModuleContentField,
                'definition_id__in',
                (descriptor.location.url() for descriptor in self.descriptors),
                field_name__in=set(field.name for field in fields),
            )
        elif scope == Scope.settings:
            return self._chunked_query(
                XModuleSettingsField,
                'usage_id__in',
                (
                    '%s-%s' % (self.course_id, descriptor.location.url())
                    for descriptor in self.descriptors
                ),
                field_name__in=set(field.name for field in fields),
            )
        elif scope == Scope.preferences:
            return self._chunked_query(
                XModuleStudentPrefsField,
                'module_type__in',
                set(descriptor.module_class.__name__ for descriptor in self.descriptors),
                student=self.user.pk,
                field_name__in=set(field.name for field in fields),
            )
        elif scope == Scope.user_info:
            return self._query(
                XModuleStudentInfoField,
                student=self.user.pk,
                field_name__in=set(field.name for field in fields),
            )
        else:
            raise InvalidScopeError(scope)

    def _fields_to_cache(self):
        """
        Returns a map of scopes to fields in that scope that should be cached
        """
        scope_map = defaultdict(set)
        for descriptor in self.descriptors:
            for field in (descriptor.module_class.fields + descriptor.module_class.lms.fields):
                scope_map[field.scope].add(field)
        return scope_map

    def _cache_key_from_kvs_key(self, key):
        """
        Return the key used in the ModelDataCache for the specified KeyValueStore key
        """
        if key.scope == Scope.user_state:
            return (key.scope, key.block_scope_id.url())
        elif key.scope == Scope.content:
            return (key.scope, key.block_scope_id.url(), key.field_name)
        elif key.scope == Scope.settings:
            return (key.scope, '%s-%s' % (self.course_id, key.block_scope_id.url()), key.field_name)
        elif key.scope == Scope.preferences:
            return (key.scope, key.block_scope_id, key.field_name)
        elif key.scope == Scope.user_info:
            return (key.scope, key.field_name)

    def _cache_key_from_field_object(self, scope, field_object):
        """
        Return the key used in the ModelDataCache for the specified scope and
        field
        """
        if scope == Scope.user_state:
            return (scope, field_object.module_state_key)
        elif scope == Scope.content:
            return (scope, field_object.definition_id, field_object.field_name)
        elif scope == Scope.settings:
            return (scope, field_object.usage_id, field_object.field_name)
        elif scope == Scope.preferences:
            return (scope, field_object.module_type, field_object.field_name)
        elif scope == Scope.user_info:
            return (scope, field_object.field_name)

    def find(self, key):
        '''
        Look for a model data object using an LmsKeyValueStore.Key object

        key: An `LmsKeyValueStore.Key` object selecting the object to find

        returns the found object, or None if the object doesn't exist
        '''
        return self.cache.get(self._cache_key_from_kvs_key(key))

    def find_or_create(self, key):
        '''
        Find a model data object in this cache, or create it if it doesn't
        exist
        '''
        field_object = self.find(key)

        if field_object is not None:
            return field_object

        if key.scope == Scope.user_state:
            field_object, _ = StudentModule.objects.get_or_create(
                course_id=self.course_id,
                student=self.user,
                module_state_key=key.block_scope_id.url(),
                defaults={'state': json.dumps({}),
                          'module_type': key.block_scope_id.category,
                         },
            )
        elif key.scope == Scope.content:
            field_object, _ = XModuleContentField.objects.get_or_create(
                field_name=key.field_name,
                definition_id=key.block_scope_id.url()
            )
        elif key.scope == Scope.settings:
            field_object, _ = XModuleSettingsField.objects.get_or_create(
                field_name=key.field_name,
                usage_id='%s-%s' % (self.course_id, key.block_scope_id.url()),
            )
        elif key.scope == Scope.preferences:
            field_object, _ = XModuleStudentPrefsField.objects.get_or_create(
                field_name=key.field_name,
                module_type=key.block_scope_id,
                student=self.user,
            )
        elif key.scope == Scope.user_info:
            field_object, _ = XModuleStudentInfoField.objects.get_or_create(
                field_name=key.field_name,
                student=self.user,
            )

        cache_key = self._cache_key_from_kvs_key(key)
        self.cache[cache_key] = field_object
        return field_object


class LmsKeyValueStore(KeyValueStore):
    """
    This KeyValueStore will read data from descriptor_model_data if it exists,
    but will not overwrite any keys set in descriptor_model_data. Attempts to do so will
    raise an InvalidWriteError.

    If the scope to write to is not one of the 5 named scopes:
        Scope.content
        Scope.settings
        Scope.user_state
        Scope.preferences
        Scope.user_info
    then an InvalidScopeError will be raised.

    Data for Scope.user_state is stored as StudentModule objects via the django orm.

    Data for the other scopes is stored in individual objects that are named for the
    scope involved and have the field name as a key

    If the key isn't found in the expected table during a read or a delete, then a KeyError will be raised
    """

    _allowed_scopes = (
        Scope.content,
        Scope.settings,
        Scope.user_state,
        Scope.preferences,
        Scope.user_info,
        Scope.children,
    )

    def __init__(self, descriptor_model_data, model_data_cache):
        self._descriptor_model_data = descriptor_model_data
        self._model_data_cache = model_data_cache

    def get(self, key):
        if key.field_name in self._descriptor_model_data:
            return self._descriptor_model_data[key.field_name]

        if key.scope == Scope.parent:
            return None

        if key.scope not in self._allowed_scopes:
            raise InvalidScopeError(key.scope)

        field_object = self._model_data_cache.find(key)
        if field_object is None:
            raise KeyError(key.field_name)

        if key.scope == Scope.user_state:
            return json.loads(field_object.state)[key.field_name]
        else:
            return json.loads(field_object.value)

    def set(self, key, value):
        if key.field_name in self._descriptor_model_data:
            raise InvalidWriteError("Not allowed to overwrite descriptor model data", key.field_name)

        field_object = self._model_data_cache.find_or_create(key)

        if key.scope not in self._allowed_scopes:
            raise InvalidScopeError(key.scope)

        if key.scope == Scope.user_state:
            state = json.loads(field_object.state)
            state[key.field_name] = value
            field_object.state = json.dumps(state)
        else:
            field_object.value = json.dumps(value)

        field_object.save()

    def delete(self, key):
        if key.field_name in self._descriptor_model_data:
            raise InvalidWriteError("Not allowed to deleted descriptor model data", key.field_name)

        if key.scope not in self._allowed_scopes:
            raise InvalidScopeError(key.scope)

        field_object = self._model_data_cache.find(key)
        if field_object is None:
            raise KeyError(key.field_name)

        if key.scope == Scope.user_state:
            state = json.loads(field_object.state)
            del state[key.field_name]
            field_object.state = json.dumps(state)
            field_object.save()
        else:
            field_object.delete()

    def has(self, key):
        if key.field_name in self._descriptor_model_data:
            return key.field_name in self._descriptor_model_data

        if key.scope == Scope.parent:
            return True

        if key.scope not in self._allowed_scopes:
            raise InvalidScopeError(key.scope)

        field_object = self._model_data_cache.find(key)
        if field_object is None:
            return False

        if key.scope == Scope.user_state:
            return key.field_name in json.loads(field_object.state)
        else:
            return True


LmsUsage = namedtuple('LmsUsage', 'id, def_id')
