"""A very basic toy runtime for XBlock tests."""

from __future__ import absolute_import, division, print_function, unicode_literals

import logging

try:
    import simplejson as json
except ImportError:
    import json

import six

from xblock.fields import Scope
from xblock.runtime import (
    KvsFieldData, KeyValueStore, Runtime, MemoryIdManager
)
from xblock.test.tools import unabc

log = logging.getLogger(__name__)


class ToyRuntimeKeyValueStore(KeyValueStore):
    """A `KeyValueStore` for the ToyRuntime to use.

    This is a simple `KeyValueStore` which stores everything in a dictionary.
    The key mapping is a little complicated to make it somewhat possible to
    read the dict when it is rendered in the browser.

    """
    def __init__(self, db_dict):
        super(ToyRuntimeKeyValueStore, self).__init__()
        self.db_dict = db_dict

    # ToyRuntime-special methods.

    def clear(self):
        """Clear all data from the store."""
        self.db_dict.clear()

    def as_json(self):
        """Render the key value store to JSON."""
        keyvaluestore_json = json.dumps(self.db_dict, sort_keys=True, indent=4)
        return keyvaluestore_json

    # Implementation details.

    def _actual_key(self, key):
        """
        Constructs the full key name from the given `key`.

        The actual key consists of the scope, block scope id, and user_id.

        """
        key_list = []
        if key.scope == Scope.children:
            key_list.append('children')
        elif key.scope == Scope.parent:
            key_list.append('parent')
        else:
            key_list.append(key.scope.block.attr_name)

        if key.block_scope_id is not None:
            key_list.append(key.block_scope_id)
        if key.user_id:
            key_list.append(key.user_id)
        return ".".join(key_list)

    # KeyValueStore methods.

    def get(self, key):
        return self.db_dict[self._actual_key(key)][key.field_name]

    def set(self, key, value):
        """Sets the key to the new value"""
        self.db_dict.setdefault(self._actual_key(key), {})[key.field_name] = value

    def delete(self, key):
        del self.db_dict[self._actual_key(key)][key.field_name]

    def has(self, key):
        return key.field_name in self.db_dict[self._actual_key(key)]

    def set_many(self, update_dict):
        """
        Sets many fields to new values in one call.

        `update_dict`: A dictionary of keys: values.
        This method sets the value of each key to the specified new value.
        """
        for key, value in six.iteritems(update_dict):
            # We just call `set` directly here, because this is an in-memory representation
            # thus we don't concern ourselves with bulk writes.
            self.set(key, value)


@unabc("{} is unavailable in ToyRuntime")
class ToyRuntime(Runtime):
    """
    Access to the toy runtime environment for XBlocks.

    A pre-configured instance of this class will be available to XBlocks as
    `self.runtime`.

    """
    # pylint: disable=abstract-method

    def __init__(self, user_id=None):
        super(ToyRuntime, self).__init__(ID_MANAGER, services={'field-data': KvsFieldData(TOYRUNTIME_KVS)})
        self.id_generator = ID_MANAGER
        self.user_id = user_id

    def render_template(self, template_name, **kwargs):  # pylint: disable=unused-argument
        """Mock for rendering templates"""
        return template_name

    def handler_url(self, block, handler_name, suffix='', query='', thirdparty=False):
        # Be sure this really is a handler.
        func = getattr(block, handler_name, None)
        if not func:
            raise ValueError("{!r} is not a function name".format(handler_name))
        if not getattr(func, "_is_xblock_handler", False):
            raise ValueError("{!r} is not a handler name".format(handler_name))

        url = ''

        has_query = False
        if not thirdparty:
            url += "?student={student}".format(student=block.scope_ids.user_id)
            has_query = True
        if query:
            url += "&" if has_query else "?"
            url += query
        return url

    def resource_url(self, resource):
        return "toyruntime/" + resource

    def local_resource_url(self, block, uri):
        return ''

    def publish(self, block, event_type, event_data):
        log.info(
            "XBlock '%s' event for %s (usage_id={%s}): %r",
            event_type,
            block.scope_ids.block_type,
            block.scope_ids.usage_id,
            event_data
        )


# Our global state (the "database").
TOYRUNTIME_KVS = ToyRuntimeKeyValueStore(dict())

# Our global id manager
ID_MANAGER = MemoryIdManager()
