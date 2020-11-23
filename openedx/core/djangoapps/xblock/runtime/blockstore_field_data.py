"""
Key-value store that holds XBlock field data read out of Blockstore
"""

from collections import namedtuple
from weakref import WeakKeyDictionary
import logging

from xblock.exceptions import InvalidScopeError, NoSuchDefinition
from xblock.fields import Field, BlockScope, Scope, UserScope, Sentinel
from xblock.field_data import FieldData

from openedx.core.djangoapps.xblock.learning_context.manager import get_learning_context_impl
from openedx.core.djangolib.blockstore_cache import (
    get_bundle_version_files_cached,
    get_bundle_draft_files_cached,
)

log = logging.getLogger(__name__)

ActiveBlock = namedtuple('ActiveBlock', ['olx_hash', 'changed_fields'])

DELETED = Sentinel('DELETED')  # Special value indicating a field was reset to its default value
CHILDREN_INCLUDES = Sentinel('CHILDREN_INCLUDES')  # Key for a pseudo-field that stores the XBlock's children info

MAX_DEFINITIONS_LOADED = 100  # How many of the most recently used XBlocks' field data to keep in memory at max.


class BlockInstanceUniqueKey(object):
    """
    An empty object used as a unique key for each XBlock instance, see
    get_weak_key_for_block() and BlockstoreFieldData._get_active_block(). Every
    XBlock instance will get a unique one of these keys, even if they are
    otherwise identical. Its purpose is similar to `id(block)`.
    """


def get_weak_key_for_block(block):
    """
    Given an XBlock instance, return an object with the same lifetime as the
    block, suitable as a key to hold block-specific data in a WeakKeyDictionary.
    """
    # We would like to make the XBlock instance 'block' itself the key of
    # BlockstoreFieldData.active_blocks, so that we have exactly one entry per
    # XBlock instance in memory, and they'll each be automatically freed by the
    # WeakKeyDictionary as needed. But because XModules implement
    # __eq__() in a way that reads all field values, just attempting to use
    # the block as a dict key here will trigger infinite recursion. So
    # instead we key the dict on an arbitrary object,
    # block key = BlockInstanceUniqueKey() which we create here. That way
    # the weak reference will still cause the entry in the WeakKeyDictionary to
    # be freed automatically when the block is no longer needed, and we
    # still get one entry per XBlock instance.
    if not hasattr(block, '_field_data_key_obj'):
        block._field_data_key_obj = BlockInstanceUniqueKey()  # pylint: disable=protected-access
    return block._field_data_key_obj  # pylint: disable=protected-access


def get_olx_hash_for_definition_key(def_key):
    """
    Given a BundleDefinitionLocator, which identifies a specific version of an
    OLX file, return the hash of the OLX file as given by the Blockstore API.
    """
    if def_key.bundle_version:
        # This is referring to an immutable file (BundleVersions are immutable so this can be aggressively cached)
        files_list = get_bundle_version_files_cached(def_key.bundle_uuid, def_key.bundle_version)
    else:
        # This is referring to a draft OLX file which may be recently updated:
        files_list = get_bundle_draft_files_cached(def_key.bundle_uuid, def_key.draft_name)
    for entry in files_list:
        if entry.path == def_key.olx_path:
            return entry.hash_digest
    raise NoSuchDefinition("Could not load OLX file for key {}".format(def_key))


class BlockstoreFieldData(FieldData):
    """
    An XBlock FieldData implementation that reads XBlock field data directly out
    of Blockstore.

    It requires that every XBlock have a BundleDefinitionLocator as its
    "definition key", since the BundleDefinitionLocator is what specifies the
    OLX file path and version to use.

    Within Blockstore there is no mechanism for setting different field values
    at the usage level compared to the definition level, so we treat
    usage-scoped fields identically to definition-scoped fields.
    """
    def __init__(self):
        """
        Initialize this BlockstoreFieldData instance.
        """
        # loaded definitions: a dict where the key is the hash of the XBlock's
        # olx file (as stated by the Blockstore API), and the values is the
        # dict of field data as loaded from that OLX file. The field data dicts
        # in this should be considered immutable, and never modified.
        self.loaded_definitions = {}
        # Active blocks: this holds the field data *changes* for all the XBlocks
        # that are currently in memory being used for something. We only keep a
        # weak reference so that the memory will be freed when the XBlock is no
        # longer needed (e.g. at the end of a request)
        # The key of this dictionary is on ID object owned by the XBlock itself
        # (see _get_active_block()) and the value is an ActiveBlock object
        # (which holds olx_hash and changed_fields)
        self.active_blocks = WeakKeyDictionary()
        super(BlockstoreFieldData, self).__init__()

    def _getfield(self, block, name):
        """
        Return the field with the given `name` from `block`.
        If the XBlock doesn't have such a field, raises a KeyError.
        """
        # First, get the field from the class, if defined
        block_field = getattr(block.__class__, name, None)
        if block_field is not None and isinstance(block_field, Field):
            return block_field
        # Not in the class, so name really doesn't name a field
        raise KeyError(name)

    def _check_field(self, block, name):
        """
        Given a block and the name of one of its fields, check that we will be
        able to read/write it.
        """
        if name == CHILDREN_INCLUDES:
            return  # This is a pseudo-field used in conjunction with BlockstoreChildrenData
        field = self._getfield(block, name)
        if field.scope in (Scope.children, Scope.parent):
            # This field data store is focused on definition-level field data, and children/parent is mostly
            # relevant at the usage level. Scope.parent doesn't even seem to be used?
            raise NotImplementedError("Setting Scope.children/parent is not supported by BlockstoreFieldData.")
        else:
            if field.scope.user != UserScope.NONE:
                raise InvalidScopeError("BlockstoreFieldData only supports UserScope.NONE fields")
            if field.scope.block not in (BlockScope.DEFINITION, BlockScope.USAGE):
                raise InvalidScopeError(
                    "BlockstoreFieldData does not support BlockScope.{} fields".format(field.scope.block)
                )
            # There is also BlockScope.TYPE but we don't need to support that;
            # it's mostly relevant as Scope.preferences(UserScope.ONE, BlockScope.TYPE)
            # Which would be handled by a user-aware FieldData implementation

    def _get_active_block(self, block):
        """
        Get the ActiveBlock entry for the specified block, creating it if
        necessary.
        """
        key = get_weak_key_for_block(block)
        if key not in self.active_blocks:
            self.active_blocks[key] = ActiveBlock(
                olx_hash=get_olx_hash_for_definition_key(block.scope_ids.def_id),
                changed_fields={},
            )
        return self.active_blocks[key]

    def get(self, block, name):
        """
        Get the given field value from Blockstore

        If the XBlock has been making changes to its fields, the value will be
        in self._get_active_block(block).changed_fields[name]

        Otherwise, the value comes from self.loaded_definitions which is a dict
        of OLX file field data, keyed by the hash of the OLX file.
        """
        self._check_field(block, name)
        entry = self._get_active_block(block)
        if name in entry.changed_fields:
            value = entry.changed_fields[name]
            if value == DELETED:
                raise KeyError  # KeyError means use the default value, since this field was deliberately set to default
            return value
        try:
            saved_fields = self.loaded_definitions[entry.olx_hash]
        except KeyError:
            if name == CHILDREN_INCLUDES:
                # Special case: parse_xml calls add_node_as_child which calls 'block.children.append()'
                # BEFORE parse_xml is done, and .append() needs to read the value of children. So
                return []  # start with an empty list, it will get filled in.
            # Otherwise, this is an anomalous get() before the XML was fully loaded:
            # This could happen if an XBlock's parse_xml() method tried to read a field before setting it,
            # if an XBlock read field data in its constructor (forbidden), or if an XBlock was loaded via
            # some means other than runtime.get_block(). One way this can happen is if you log/print an XBlock during
            # XML parsing, because ScopedStorageMixin.__repr__ will try to print all field values, and any fields which
            # aren't mentioned in the XML (which are left at their default) will be "not loaded yet."
            log.exception(
                "XBlock %s tried to read from field data (%s) that wasn't loaded from Blockstore!",
                block.scope_ids.usage_id, name,
            )
            raise  # Just use the default value for now; any exception raised here is caught anyways
        return saved_fields[name]
        # If 'name' is not found, this will raise KeyError, which means to use the default value

    def set(self, block, name, value):
        """
        Set the value of the field named `name`
        """
        entry = self._get_active_block(block)
        entry.changed_fields[name] = value

    def delete(self, block, name):
        """
        Reset the value of the field named `name` to the default
        """
        self.set(block, name, DELETED)

    def default(self, block, name):
        """
        Get the default value for block's field 'name'.
        The XBlock class will provide the default if KeyError is raised; this is
        mostly for the purpose of context-specific overrides.
        """
        raise KeyError(name)

    def cache_fields(self, block):
        """
        Cache field data:
        This is called by the runtime after a block has parsed its OLX via its
        parse_xml() methods and written all of its field values into this field
        data store. The values will be stored in
            self._get_active_block(block).changed_fields
        so we know at this point that that isn't really "changed" field data,
        it's the result of parsing the OLX. Save a copy into loaded_definitions.
        """
        entry = self._get_active_block(block)
        self.loaded_definitions[entry.olx_hash] = entry.changed_fields.copy()
        # Reset changed_fields to indicate this block hasn't actually made any field data changes, just loaded from XML:
        entry.changed_fields.clear()

        if len(self.loaded_definitions) > MAX_DEFINITIONS_LOADED:
            self.free_unused_definitions()

    def has_changes(self, block):
        """
        Does the specified block have any unsaved changes?
        """
        entry = self._get_active_block(block)
        return bool(entry.changed_fields)

    def has_cached_definition(self, definition_key):
        """
        Has the specified OLX file been loaded into memory?
        """
        olx_hash = get_olx_hash_for_definition_key(definition_key)
        return olx_hash in self.loaded_definitions

    def free_unused_definitions(self):
        """
        Free unused field data cache entries from self.loaded_definitions
        as long as they're not in use.
        """
        olx_hashes = set(self.loaded_definitions.keys())
        olx_hashes_needed = set(entry.olx_hash for entry in self.active_blocks.values())

        olx_hashes_safe_to_delete = olx_hashes - olx_hashes_needed

        # To avoid doing this too often, randomly cull unused entries until
        # we have only half as many as MAX_DEFINITIONS_LOADED in memory, if possible.
        while olx_hashes_safe_to_delete and (len(self.loaded_definitions) > MAX_DEFINITIONS_LOADED / 2):
            del self.loaded_definitions[olx_hashes_safe_to_delete.pop()]


class BlockstoreChildrenData(FieldData):
    """
    An XBlock FieldData implementation that reads 'children' data out of
    the definition fields in BlockstoreFieldData.

    The children field contains usage keys and so is usage-specific; the
    BlockstoreFieldData can only store field data that is not usage-specific. So
    we store data about the <xblock-include /> elements that define the children
    in BlockstoreFieldData (since that is not usage-specific), and this field
    data implementation loads that <xblock-include /> data and transforms it
    into the usage keys that comprise the standard .children field.
    """
    def __init__(self, blockstore_field_data):
        """
        Initialize this BlockstoreChildrenData instance.
        """
        # The data store that holds Scope.usage and Scope.definition data:
        self.authored_data_store = blockstore_field_data
        super(BlockstoreChildrenData, self).__init__()

    def _check_field(self, block, name):  # pylint: disable=unused-argument
        """
        Given a block and the name of one of its fields, check that we will be
        able to read/write it.
        """
        if name != 'children':
            raise InvalidScopeError("BlockstoreChildrenData can only read/write from a field named 'children'")

    def get(self, block, name):
        """
        Get the "children' field value.

        We do this by reading the parsed <xblock-include /> values from
        the regular authored data store and then transforming them to usage IDs.
        """
        self._check_field(block, name)
        children_includes = self.get_includes(block)
        if not children_includes:
            return []
        # Now the .children field is required to be a list of usage IDs:
        learning_context = get_learning_context_impl(block.scope_ids.usage_id)
        child_usages = []
        for parsed_include in children_includes:
            child_usages.append(
                learning_context.usage_for_child_include(
                    block.scope_ids.usage_id, block.scope_ids.def_id, parsed_include,
                )
            )
        return child_usages

    def set(self, block, name, value):
        """
        Set the value of the field; requires name='children'
        """
        self._check_field(block, name)
        children_includes = self.authored_data_store.get(block, CHILDREN_INCLUDES)
        if len(value) != len(children_includes):
            raise RuntimeError(
                "This runtime does not allow changing .children directly - use runtime.add_child_include instead."
            )
        # This is a no-op; the value of 'children' is derived from CHILDREN_INCLUDES
        # so we never write to the children field directly. All we do is make sure it
        # looks like it's still in sync with CHILDREN_INCLUDES

    def get_includes(self, block):
        """
        Get the list of <xblock-include /> elements representing this XBlock's
        children.
        """
        try:
            return self.authored_data_store.get(block, CHILDREN_INCLUDES)
        except KeyError:
            # KeyError raised by an XBlock field data store means "use the
            # default value", and the default value for the children field is an
            # empty list.
            return []

    def append_include(self, block, parsed_include):
        """
        Append an <xblock-include /> element to this XBlock's list of children
        """
        self.authored_data_store.set(block, CHILDREN_INCLUDES, self.get_includes(block) + [parsed_include])

    def delete(self, block, name):
        """
        Reset the value of the field named `name` to the default
        """
        self._check_field(block, name)
        self.authored_data_store.set(block, CHILDREN_INCLUDES, [])
        self.set(block, name, [])
