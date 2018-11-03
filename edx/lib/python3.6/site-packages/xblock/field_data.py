"""
A :class:`FieldData` is used by :class:`~xblock.core.XBlock` to read and write
data to particular scoped fields by name. This allows individual runtimes to
provide varied persistence backends while keeping the API used by the `XBlock`
simple.
"""

from __future__ import absolute_import, division, print_function, unicode_literals


import copy

from abc import ABCMeta, abstractmethod
from collections import defaultdict

import six

from xblock.exceptions import InvalidScopeError


class FieldData(six.with_metaclass(ABCMeta, object)):
    """
    An interface allowing access to an XBlock's field values indexed by field names.
    """

    @abstractmethod
    def get(self, block, name):
        """
        Retrieve the value for the field named `name` for the XBlock `block`.

        If no value is set, raise a `KeyError`.

        The value returned may be mutated without modifying the backing store.

        :param block: block to inspect
        :type block: :class:`~xblock.core.XBlock`
        :param name: field name to look up
        :type name: str
        """
        raise NotImplementedError

    @abstractmethod
    def set(self, block, name, value):
        """
        Set the value of the field named `name` for XBlock `block`.

        `value` may be mutated after this call without affecting the backing store.

        :param block: block to modify
        :type block: :class:`~xblock.core.XBlock`
        :param name: field name to set
        :type name: str
        :param value: value to set
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, block, name):
        """
        Reset the value of the field named `name` to the default for XBlock `block`.

        :param block: block to modify
        :type block: :class:`~xblock.core.XBlock`
        :param name: field name to delete
        :type name: str
        """
        raise NotImplementedError

    def has(self, block, name):
        """
        Return whether or not the field named `name` has a non-default value for the XBlock `block`.

        :param block: block to check
        :type block: :class:`~xblock.core.XBlock`
        :param name: field name
        :type name: str
        """
        try:
            self.get(block, name)
            return True
        except KeyError:
            return False

    def set_many(self, block, update_dict):
        """
        Update many fields on an XBlock simultaneously.

        :param block: the block to update
        :type block: :class:`~xblock.core.XBlock`
        :param update_dict: A map of field names to their new values
        :type update_dict: dict
        """
        for key, value in six.iteritems(update_dict):
            self.set(block, key, value)

    def default(self, block, name):  # pylint: disable=unused-argument
        """
        Get the default value for this field which may depend on context or may just be the field's global
        default. The default behavior is to raise KeyError which will cause the caller to return the field's
        global default.

        :param block: the block containing the field being defaulted
        :type block: :class:`~xblock.core.XBlock`
        :param name: the field's name
        :type name: `str`
        """
        raise KeyError(repr(name))


class DictFieldData(FieldData):
    """
    A FieldData that uses a single supplied dictionary to store fields by name.
    """
    def __init__(self, data):
        self._data = data

    def get(self, block, name):
        return copy.deepcopy(self._data[name])

    def set(self, block, name, value):
        self._data[name] = copy.deepcopy(value)

    def delete(self, block, name):
        del self._data[name]

    def has(self, block, name):
        return name in self._data

    def set_many(self, block, update_dict):
        self._data.update(copy.deepcopy(update_dict))


class SplitFieldData(FieldData):
    """
    A FieldData that uses divides particular scopes between
    several backing FieldData objects.
    """

    def __init__(self, scope_mappings):
        """
        `scope_mappings` defines :class:`~xblock.field_data.FieldData` objects to use
        for each scope. If a scope is not a key in `scope_mappings`, then using
        a field of that scope will raise an :class:`~xblock.exceptions.InvalidScopeError`.

        :param scope_mappings: A map from Scopes to backing FieldData instances
        :type scope_mappings: `dict` of :class:`~xblock.fields.Scope` to :class:`~xblock.field_data.FieldData`
        """
        self._scope_mappings = scope_mappings

    def _field_data(self, block, name):
        """Return the field data for the field `name` on the :class:`~xblock.core.XBlock` `block`"""
        scope = block.fields[name].scope

        if scope not in self._scope_mappings:
            raise InvalidScopeError(scope)

        return self._scope_mappings[scope]

    def get(self, block, name):
        return self._field_data(block, name).get(block, name)

    def set(self, block, name, value):
        self._field_data(block, name).set(block, name, value)

    def set_many(self, block, update_dict):
        update_dicts = defaultdict(dict)
        for key, value in six.iteritems(update_dict):
            update_dicts[self._field_data(block, key)][key] = value
        for field_data, new_update_dict in six.iteritems(update_dicts):
            field_data.set_many(block, new_update_dict)

    def delete(self, block, name):
        self._field_data(block, name).delete(block, name)

    def has(self, block, name):
        return self._field_data(block, name).has(block, name)

    def default(self, block, name):
        return self._field_data(block, name).default(block, name)


class ReadOnlyFieldData(FieldData):
    """
    A FieldData that wraps another FieldData an makes all calls to set and delete
    raise :class:`~xblock.exceptions.InvalidScopeError`s.
    """
    def __init__(self, source):
        self._source = source

    def get(self, block, name):
        return self._source.get(block, name)

    def set(self, block, name, value):
        raise InvalidScopeError("{block}.{name} is read-only, cannot set".format(block=block, name=name))

    def delete(self, block, name):
        raise InvalidScopeError("{block}.{name} is read-only, cannot delete".format(block=block, name=name))

    def has(self, block, name):
        return self._source.has(block, name)

    def default(self, block, name):
        return self._source.default(block, name)

    def __repr__(self):
        return "ReadOnlyFieldData({!r})".format(self._source)
