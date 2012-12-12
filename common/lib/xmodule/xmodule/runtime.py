from collections import MutableMapping, namedtuple

from .model import ModuleScope, ModelType


class KeyValueStore(object):
    """The abstract interface for Key Value Stores."""

    # Keys are structured to retain information about the scope of the data.
    # Stores can use this information however they like to store and retrieve
    # data.
    Key = namedtuple("Key", "scope, student_id, module_scope_id, field_name")

    def get(key):
        pass

    def set(key, value):
        pass

    def delete(key):
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

    def __str__(self):
        return str(dict(self.iteritems()))

    def _getfield(self, name):
        if (not hasattr(self._module_cls, name) or
            not isinstance(getattr(self._module_cls, name), ModelType)):

            raise KeyError(name)

        return getattr(self._module_cls, name)

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
            module_id = self.module_type.__name__

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
            fields.extend(field.name for field in getattr(self._module_cls, namespace_name))
        return fields
