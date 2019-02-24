"""
Key-value store that holds XBlock field data read out of Blockstore
"""
from __future__ import absolute_import, division, print_function, unicode_literals
from contextlib import contextmanager
import logging

from xblock.fields import Scope
from xblock.runtime import KeyValueStore

# The XBlock API does not contain a mechanism for reading XBlock data
# (block IDs and field data) out of XML. Instead, it only has the
# parse_xml family of methods which read XML, initialize XBlocks based
# on the XML and assign them _new_ IDs, then use the XBlock field API
# to write new values into each XBlock field based on the XML content.

# This means that without any optimization, merely trying to _read_
# XBlock data from XML will result in a whole bunch of field _writes_.
# There is no simple way to distinguish these 'writes' upon XML parsing
# from 'normal' writes wherein the XBlock chooses to modify field values.

# In order to work around this situation without changing the API, we
# require all field reads and/or writes to be part of a
# blockstore_transaction() context; that context is mostly used to know
# when we're using field data, and when it exits the in-memory cache
# is erased. More importantly, all field _writes_ must be wrapped in
# either a collect_changes() or a collect_parsed_fields() context.

# The collect_parsed_fields() context should be used when parsing,
# and it means that writes will be considered to be reads in disguise
# (we're setting the value in memory to match the value in the XML).

# The collect_changes() context should be used when running any
# XBlock view or handler, and it signifies that writes are deliberate
# changes.

log = logging.getLogger(__name__)

_cached_keys = {}  # Values that we read out of XML during a transaction, and/or committed writes
_transaction_depth = 0  # This is > 0 inside a blockstore_transaction() context
_pending_writes = []  # Values that have been written by the XBlock but not yet persisted


@contextmanager
def blockstore_transaction():
    global _transaction_depth
    _transaction_depth = _transaction_depth + 1
    try:
        yield
    except:
        raise
    finally:
        _transaction_depth = _transaction_depth - 1
        if _transaction_depth == 0:
            _cached_keys.clear()


@contextmanager
def collect_parsed_fields():
    """
    Use this context manager while parsing XBlock XML.
    All field writes are assumed to be converting data
    from XML to Python, and NOT reflecting deliberate
    changes made to field values.
    """
    if _transaction_depth < 1:
        raise RuntimeError("You need to be in a blockstore_transaction() context.")
    new_keys = {}
    _pending_writes.append(new_keys)
    try:
        yield
        # Now save all new_keys into _cached_keys:
        for key, value in new_keys.iteritems():
            _cached_keys[key] = value
    except:
        raise
    finally:
        _pending_writes.pop()  # Discard all changes


@contextmanager
def collect_changes():
    """
    Use this context manager while running an XBlock view or handler that
    may be saving new field values to Blockstore. Changes will be collected and
    then when this context manager exists, the changes will be persisted to
    blockstore in an atomic transaction.

    This is not needed when only user state fields are changing.
    """
    if _transaction_depth < 1:
        raise RuntimeError("You need to be in a blockstore_transaction() context.")
    new_keys = {}
    _pending_writes.append(new_keys)
    try:
        yield
        # TODO: Now persist all changes to Blockstore
        for key, value in new_keys.iteritems():
            log.warning(
                "Block field '%s' has changed to '%s' but persisting changes is not yet implemented.",
                key, value,
            )
        # Now save all new_keys into _cached_keys:
        for key, value in new_keys.iteritems():
            _cached_keys[key] = value
    except:
        raise
    finally:
        _pending_writes.pop()  # Discard all changes


class BlockstoreKVS(KeyValueStore):
    """
    A KeyValueStore that reads XBlock field data directly out of Blockstore.
    Note that this is considered too slow for use in the LMS, but is fine
    for authoring.
    """

    VALID_SCOPES = (Scope.parent, Scope.children, Scope.settings, Scope.content)

    def __init__(self):
        """
        Initialize the Blockstore KVS. This is long-lived object and
        can be used as a singleton - only one instance is ever needed.
        """

    def get(self, key):
        if _transaction_depth < 1:
            raise RuntimeError(
                "You need to be in a blockstore_transaction() context to access blockstore-backed fields"
            )
        for cache in reversed(_pending_writes):
            if key in cache:
                return cache[key]
        return _cached_keys[key]  # If not found in here, this line will raise KeyError() to use the default value

    def set(self, key, value):
        if not _pending_writes:
            raise RuntimeError("Cannot modify fields outside of a collect_changes() or collect_parsed_fields() context")
        _pending_writes[-1][key] = value

    def delete(self, key):
        raise NotImplementedError()

    def has(self, key):
        """
        Is the given field explicitly set in this kvs (neither inherited nor default)
        """
        # handle any special cases
        if key.scope not in self.VALID_SCOPES:
            return False
        try:
            self.get(key)
            return True
        except KeyError:
            return False

    def default(self, key):
        """
        Get the default value for this field which may depend on context or may just be the field's global
        default. The default behavior is to raise KeyError which will cause the caller to return the field's
        global default.
        """
        raise KeyError()
