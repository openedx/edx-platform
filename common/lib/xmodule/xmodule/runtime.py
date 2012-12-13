from collections import MutableMapping, namedtuple

from .model import ModuleScope, ModelType


class KeyValueStore(object):
    """The abstract interface for Key Value Stores."""

    # Keys are structured to retain information about the scope of the data.
    # Stores can use this information however they like to store and retrieve
    # data.
    Key = namedtuple("Key", "scope, student_id, module_scope_id, field_name")

    def get(self, key):
        pass

    def set(self, key, value):
        pass

    def delete(self, key):
        pass


class DbModel(MutableMapping):
    """A dictionary-like interface to the fields on a module."""

    def __init__(self, kvs, module_cls, student_id, usage):
        self._kvs = kvs
        self._student_id = student_id
        self._module_cls = module_cls
        self._usage = usage

    def __repr__(self):
        return "<{0.__class__.__name__} {0._module_cls!r}>".format(self)

    def _getfield(self, name):
        # First, get the field from the class, if defined
        module_field = getattr(self._module_cls, name, None)
        if module_field is not None and isinstance(module_field, ModelType):
            return module_field

        # If the class doesn't have the field, and it also
        # doesn't have any namespaces, then the the name isn't a field
        # so KeyError
        if not hasattr(self._module_cls, 'namespaces'):
            return KeyError(name)

        # Resolve the field name in the first namespace where it's
        # available
        for namespace_name in self._module_cls.namespaces:
            namespace = getattr(self._module_cls, namespace_name)
            namespace_field = getattr(type(namespace), name, None)
            if namespace_field is not None and isinstance(namespace_field, ModelType):
                return namespace_field

        # Not in the class or in any of the namespaces, so name
        # really doesn't name a field
        raise KeyError(name)

    def _key(self, name):
        field = self._getfield(name)
        module = field.scope.module

        if module == ModuleScope.ALL:
            module_id = None
        elif module == ModuleScope.USAGE:
            module_id = self._usage.id
        elif module == ModuleScope.DEFINITION:
            module_id = self._usage.def_id
        elif module == ModuleScope.TYPE:
            module_id = self._module_cls.__name__

        if field.scope.student:
            student_id = self._student_id
        else:
            student_id = None

        key = KeyValueStore.Key(
            scope=field.scope,
            student_id=student_id,
            module_scope_id=module_id,
            field_name=name
            )
        return key

    def __getitem__(self, name):
        return self._kvs.get(self._key(name))

    def __setitem__(self, name, value):
        self._kvs.set(self._key(name), value)

    def __delitem__(self, name):
        self._kvs.delete(self._key(name))

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return len(self.keys())

    def keys(self):
        fields = [field.name for field in self._module_cls.fields]
        for namespace_name in self._module_cls.namespaces:
            fields.extend(field.name for field in getattr(self._module_cls, namespace_name).fields)
        return fields
