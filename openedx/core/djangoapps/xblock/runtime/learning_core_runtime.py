"""

"""
from __future__ import annotations

import logging
from collections import namedtuple
from datetime import datetime, timezone
from uuid import UUID
from weakref import WeakKeyDictionary

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.db.transaction import atomic

from openedx_learning.core.components import api as components_api
from openedx_learning.core.contents import api as contents_api
from openedx_learning.core.publishing import api as publishing_api

from lxml import etree
from opaque_keys.edx.keys import UsageKeyV2

from xblock.core import XBlock
from xblock.exceptions import InvalidScopeError, NoSuchDefinition, NoSuchUsage
from xblock.fields import Field, BlockScope, Scope, ScopeIds, UserScope, Sentinel
from xblock.field_data import FieldData

from opaque_keys.edx.keys import AssetKey, CourseKey, DefinitionKey, LearningContextKey, UsageKey, UsageKeyV2
from opaque_keys.edx.locator import CheckFieldMixin

from openedx.core.djangoapps.xblock.learning_context.manager import get_learning_context_impl
from openedx.core.djangoapps.xblock.runtime.runtime import XBlockRuntime
from openedx.core.djangoapps.xblock.runtime.id_managers import OpaqueKeyReader
from openedx.core.lib.xblock_serializer.api import serialize_xblock_to_olx, serialize_modulestore_block_for_blockstore

log = logging.getLogger(__name__)


DELETED = Sentinel('DELETED')  # Special value indicating a field was reset to its default value
CHILDREN_INCLUDES = Sentinel('CHILDREN_INCLUDES')  # Key for a pseudo-field that stores the XBlock's children info

MAX_DEFINITIONS_LOADED = 100  # How many of the most recently used XBlocks' field data to keep in memory at max.

ActiveBlock = namedtuple('ActiveBlock', ['olx_hash', 'changed_fields'])




class LearningCoreFieldData(FieldData):
    """
    Chunks of this are copied from BlockstoreFieldData
    """

    def __init__(self):
        """
        Initialize this BlockstoreFieldData instance.
        """
        # Both of these have UsageKeys for keys and have dicts for values.
        self.usage_keys_to_loaded_fields = {}
        self.usage_keys_to_changed_fields = {}

        super().__init__()

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
        if field.scope in (Scope.children, Scope.parent):  # lint-amnesty, pylint: disable=no-else-raise
            # This field data store is focused on definition-level field data, and children/parent is mostly
            # relevant at the usage level. Scope.parent doesn't even seem to be used?
            raise NotImplementedError("Setting Scope.children/parent is not supported by LearningCoreFieldData.")

        if field.scope.user != UserScope.NONE:
            raise InvalidScopeError("LearningCoreFieldData only supports UserScope.NONE fields")

        if field.scope.block not in (BlockScope.DEFINITION, BlockScope.USAGE):
            raise InvalidScopeError(
                f"LearningCoreFieldData does not support BlockScope.{field.scope.block} fields"
            )
            # There is also BlockScope.TYPE but we don't need to support that;
            # it's mostly relevant as Scope.preferences(UserScope.ONE, BlockScope.TYPE)
            # Which would be handled by a user-aware FieldData implementation

    def get(self, block, name):
        """
        Get the given field value from Blockstore

        If the XBlock has been making changes to its fields, the value will be
        in self._get_active_block(block).changed_fields[name]

        Otherwise, the value comes from self.loaded_definitions which is a dict
        of OLX file field data, keyed by the hash of the OLX file.
        """
        self._check_field(block, name)
        usage_key = block.scope_ids.usage_id

        # First check if it's on our dict of changed fields that haven't been
        # persisted yet.
        changed_fields = self.usage_keys_to_changed_fields.get(usage_key, {})
        if name in changed_fields:
            value = changed_fields[name]
            if value == DELETED:
                raise KeyError  # KeyError means use the default value, since this field was deliberately set to default

        try:
            loaded_fields = self.usage_keys_to_loaded_fields[usage_key]
        except KeyError:
            # If there's no entry for that usage key, then we're trying to read
            # field data from a block that was never loaded, which we don't
            # expect to happen. Log an exception for this.
            #
            # TODO: Actually, is this normal for unsaved default fields?
#            log.exception(
#                "XBlock %s tried to read from field data (%s) that wasn't loaded from Learning Core!",
#                block.scope_ids.usage_id,
#                name,
#           )
            raise

        # If 'name' is not found, this will raise KeyError, which means to use
        # the default value. This is expected–it means that we did load a block
        # for it, but the block data didn't specify a value for this particular
        # field.
        return loaded_fields[name]

    def has_changes(self, block):
        usage_key = block.scope_ids.usage_id
        changed_fields = self.usage_keys_to_changed_fields.get(usage_key, {})
        return bool(changed_fields)

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
        usage_key = block.scope_ids.usage_id
        supported_scopes = {Scope.content, Scope.settings}
        loaded_fields = {
            key: getattr(block, key)
            for key, field in block.fields.items()
            if field.scope in supported_scopes
        }
        self.usage_keys_to_loaded_fields[usage_key] = loaded_fields
        # Reset changed_fields to indicate this block hasn't actually made any field data changes, just loaded from XML:
        if usage_key in self.usage_keys_to_changed_fields:
             self.usage_keys_to_changed_fields[usage_key].clear()

        #self.usage_keys_to_loaded_fields[usage_key] = self.usage_keys_to_changed_fields[usage_key].copy()
        #self.usage_keys_to_changed_fields[usage_key].clear()


    def delete(self, block, name):
        self.set(block, name, DELETED)

    def set(self, block, name, value):
        usage_key = block.scope_ids.usage_id
        changed_fields = self.usage_keys_to_changed_fields.get(usage_key, {})
        changed_fields[name] = value
        self.usage_keys_to_changed_fields[usage_key] = changed_fields

    def default(self, block, name):
        raise KeyError(name)


class LearningCoreOpaqueKeyReader(OpaqueKeyReader):
    def get_definition_id(self, usage_id):
        """
        This is mostly here to make sure LearningCore-based things *don't* call
        it. By making it explode if it's called.
        """
        raise NotImplementedError(
            "This should never be called with the LearningCoreXBlockRuntime"
        )


class LearningCoreXBlockRuntime(XBlockRuntime):
    """
    XBlock runtime that uses openedx-learning apps for content storage.
    """
    def _get_component_from_usage_key(self, usage_key):
        """
        TODO: This is the third place where we're implementing this. Figure out
        where the definitive place should be and have everything else call that.
        """
        learning_package = publishing_api.get_learning_package_by_key(str(usage_key.lib_key))
        try:
            component = components_api.get_component_by_key(
                learning_package.id,
                namespace='xblock.v1',
                type_name=usage_key.block_type,
                local_key=usage_key.block_id,
            )
        except ObjectDoesNotExist:
            raise NoSuchUsage(usage_key)

        return component

    def _lookup_asset_url(self, block: XBlock, asset_path: str):  # pylint: disable=unused-argument
        """
        Return an absolute URL for the specified static asset file that may
        belong to this XBlock.

        e.g. if the XBlock settings have a field value like "/static/foo.png"
        then this method will be called with asset_path="foo.png" and should
        return a URL like https://cdn.none/xblock/f843u89789/static/foo.png

        If the asset file is not recognized, return None

        This is called by the XBlockRuntime superclass in the .runtime module.

        CURRENT STATUS

        Right now we're not recognizing anything. We'd need to hook up something
        to serve the static assets, and the biggest issue around that is
        figuring out the permissions that need to be applied.

        Idea: Have openedx-learning provide a simple view that will stream the
        content, but have apps explicitly subclass or wrap it with permissions
        checks and such. That way the actual logic of figuring out the
        permissions stays out of openedx-learning, since it requires access to
        tables that don't exist there.
        """
        return None

    def get_block(self, usage_key, for_parent=None):
        # We can do this more efficiently in a single query later, but for now
        # just get it the easy way.
        component = self._get_component_from_usage_key(usage_key)
        component_version = component.versioning.draft
        if component_version is None:
            raise NoSuchUsage(usage_key)

        content = component_version.contents.get(
            componentversioncontent__key="block.xml"
        )
        xml_node = etree.fromstring(content.text)
        block_type = usage_key.block_type
        keys = ScopeIds(self.user_id, block_type, None, usage_key)

        if xml_node.get("url_name", None):
            log.warning("XBlock at %s should not specify an old-style url_name attribute.", usage_key)

        block_class = self.mixologist.mix(self.load_block_type(block_type))

        if hasattr(block_class, 'parse_xml_new_runtime'):
            # This is a (former) XModule with messy XML parsing code; let its parse_xml() method continue to work
            # as it currently does in the old runtime, but let this parse_xml_new_runtime() method parse the XML in
            # a simpler way that's free of tech debt, if defined.
            # In particular, XmlMixin doesn't play well with this new runtime, so this is mostly about
            # bypassing that mixin's code.
            # When a former XModule no longer needs to support the old runtime, its parse_xml_new_runtime method
            # should be removed and its parse_xml() method should be simplified to just call the super().parse_xml()
            # plus some minor additional lines of code as needed.
            block = block_class.parse_xml_new_runtime(xml_node, runtime=self, keys=keys)
        else:
            block = block_class.parse_xml(xml_node, runtime=self, keys=keys, id_generator=None)

        # Update field data with parsed values. We can't call .save() because it will call save_block(), below.
        block.force_save_fields(block._get_fields_to_save())  # pylint: disable=protected-access
        self.system.authored_data_store.cache_fields(block)

        return block

    def save_block(self, block):
        """
        Save any pending field data values to Blockstore.

        This gets called by block.save() - do not call this directly.
        """
        if not self.system.authored_data_store.has_changes(block):
            return  # No changes, so no action needed.

        # Verify that the user has permission to write to authored data in this
        # learning context:
        if self.user is not None:
            learning_context = get_learning_context_impl(block.scope_ids.usage_id)
            if not learning_context.can_edit_block(self.user, block.scope_ids.usage_id):
                log.warning("User %s does not have permission to edit %s", self.user.username, block.scope_ids.usage_id)
                raise RuntimeError("You do not have permission to edit this XBlock")

        # TODO: Verify that there's nothing broken about using the more generic
        # serialize_xblock_to_olx call instead of the blockstore-specific one.
        # serialized = serialize_modulestore_block_for_blockstore(block)
        serialized = serialize_xblock_to_olx(block)

        now = datetime.now(tz=timezone.utc)
        usage_key = block.scope_ids.usage_id
        with atomic():
            component = self._get_component_from_usage_key(usage_key)
            block_media_type = contents_api.get_or_create_media_type(
                f"application/vnd.openedx.xblock.v1.{usage_key.block_type}+xml"
            )
            content = contents_api.get_or_create_text_content(
                component.learning_package_id,
                media_type_id=block_media_type.id,
                text=serialized.olx_str,
                created=now,
            )
            components_api.create_next_version(
                component.pk,
                title=block.display_name,
                content_to_replace={
                    "block.xml": content.id,
                },
                created=now,
            )
