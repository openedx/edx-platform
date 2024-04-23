"""
Learning Core XBlock Runtime code
"""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone

from django.core.exceptions import ObjectDoesNotExist
from django.db.transaction import atomic

from openedx_learning.core.components import api as components_api
from openedx_learning.core.contents import api as contents_api
from openedx_learning.core.publishing import api as publishing_api

from lxml import etree

from xblock.core import XBlock
from xblock.exceptions import NoSuchUsage
from xblock.fields import Field, Scope, ScopeIds
from xblock.field_data import FieldData

from openedx.core.lib.xblock_serializer.api import serialize_modulestore_block_for_blockstore
from ..learning_context.manager import get_learning_context_impl
from .runtime import XBlockRuntime


log = logging.getLogger(__name__)


class LearningCoreFieldData(FieldData):
    """
    FieldData for the Learning Core XBlock Runtime

    LearningCoreFieldData only supports the ``content`` and ``settings`` scopes.
    Any attempt to read or write fields with other scopes will raise a
    ``NotImplementedError``. This class does NOT support the parent and children
    scopes.

    LearningCoreFieldData should only live for the duration of one request. The
    interaction between LearningCoreXBlockRuntime and LearningCoreFieldData is
    as follows:

    1. LearningCoreXBlockRuntime knows how retrieve authored content data from
       the Learning Core APIs in openedx-learning. This content is stored as
       OLX, and LearningCoreXBlockRuntime won't know how to parse it into
       fields, since serialization logic can happen in the XBlock itself.
    2. LearningCoreXBlockRuntime will then invoke the block to parse the OLX and
       then force_save its field data into LearningCoreFieldData.
    3. After this point, various handler and API calls might alter fields for
       a given block using the XBlock.
    4. The main thing that LearningCoreXBlockRuntime will want to know later on
       is whether it needs to write any changes when its save_block method is
       invoked. To support this, LearningCoreFieldData needs to track which
       blocks have changes to any of their fields. See the marked_unchanged
       method docstring for more details.
    """

    def __init__(self):
        # set of UsageKeyV2 for blocks that were modified and need to be saved
        self.changed = set()
        # mapping of { UsageKeyV2 : { field_name: field_value } }
        self.field_data = defaultdict(dict)

    def mark_unchanged(self, block):
        """
        Mark a block as being unchanged (i.e. no need to write this to the DB).

        Calling set or delete on a field always marks the block with that field
        as changed, by adding its usage key to self.changed. But set() is also
        called at the very beginning, when a block is first loaded from the
        database by the LearningCoreXBlockRuntime's get_block call.

        This method exists so that LearningCoreXBlockRuntime can call it
        whenever it has either just done a get_block operation (because those
        set() calls represent the already-persisted content state), or a
        save_block operation (since those changes will have been persisted).

        This is not a standard part of the FieldData interface.
        """
        usage_key = block.scope_ids.usage_id
        if usage_key in self.changed:
            self.changed.remove(usage_key)

    def delete(self, block, name):
        """
        Delete a field value from a block.
        """
        self._check_field(block, name)
        usage_key = block.scope_ids.usage_id
        del self.field_data[usage_key][name]
        self.changed.add(usage_key)

    def get(self, block, name):
        """
        Get a field value from a block.

        Raises a KeyError if the value is not found. It is very common to raise
        this error. XBlocks have many fields with default values, and the
        FieldData is not expected to store those defaults (that information
        lives on the Field object). A FieldData subclass only has to store field
        values that have explicitly been set.
        """
        self._check_field(block, name)
        usage_key = block.scope_ids.usage_id
        return self.field_data[usage_key][name]

    def set(self, block, name, value):
        """
        Set a field for a block to a value.
        """
        self._check_field(block, name)
        usage_key = block.scope_ids.usage_id

        # Check to see if we're just setting the same value. If so, return
        # without doing anything.
        block_fields = self.field_data[usage_key]
        if (name in block_fields) and (block_fields[name] == value):
            return

        block_fields[name] = value
        self.changed.add(usage_key)

    def has_changes(self, block):
        """
        Does this block have changes that need to be persisted?
        """
        return block.scope_ids.usage_id in self.changed

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
        field = self._getfield(block, name)
        if field.scope not in (Scope.content, Scope.settings):
            raise NotImplementedError(
                f"Scope {field.scope} (field {name} of {block.scope_ids.usage_id}) "
                "is unsupported. LearningCoreFieldData only supports the content"
                " and settings scopes."
            )


class LearningCoreXBlockRuntime(XBlockRuntime):
    """
    XBlock runtime that uses openedx-learning apps for content storage.

    The superclass is doing all the hard stuff. This class only only has to
    worry about the block storage, block serialization/de-serialization, and
    (eventually) asset storage.
    """

    def get_block(self, usage_key, for_parent=None):
        """
        Fetch an XBlock from Learning Core data models.

        This method will find the OLX for the content in Learning Core, parse it
        into an XBlock (with mixins) instance, and properly initialize our
        internal LearningCoreFieldData instance with the field values from the
        parsed OLX.
        """
        # We can do this more efficiently in a single query later, but for now
        # just get it the easy way.
        component = self._get_component_from_usage_key(usage_key)
        # TODO: For now, this runtime will only be used in CMS, so it's fine to just return the Draft version.
        #       However, we will need the runtime to return the Published version for LMS (and Draft for LMS-Preview).
        #       We should base this Draft vs Published decision on a runtime initialization parameter.
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
            block = block_class.parse_xml(xml_node, runtime=self, keys=keys)

        # Update field data with parsed values. We can't call .save() because it will call save_block(), below.
        block.force_save_fields(block._get_fields_to_save())  # pylint: disable=protected-access

        # We've pre-loaded the fields for this block, so the FieldData shouldn't
        # consider these values "changed" in its sense of "you have to persist
        # these because we've altered the field values from what was stored".
        self.system.authored_data_store.mark_unchanged(block)

        return block

    def save_block(self, block):
        """
        Save any pending field data values to Learning Core data models.

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

        # We need Blockstore's serialization so we don't have `url_name` showing
        # up in all the OLX. TODO: Rename this later, after we figure out what
        # other changes we need to make in the serialization as part of the
        # Blockstore -> Learning Core conversion.
        serialized = serialize_modulestore_block_for_blockstore(block)
        now = datetime.now(tz=timezone.utc)
        usage_key = block.scope_ids.usage_id
        with atomic():
            component = self._get_component_from_usage_key(usage_key)
            block_media_type = contents_api.get_or_create_media_type(
                f"application/vnd.openedx.xblock.v1.{usage_key.block_type}+xml"
            )
            content = contents_api.get_or_create_text_content(
                component.learning_package_id,
                block_media_type.id,
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
        self.system.authored_data_store.mark_unchanged(block)

    def _get_component_from_usage_key(self, usage_key):
        """
        Note that Components aren't ever really truly deleted, so this will
        return a Component if this usage key has ever been used, even if it was
        later deleted.

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
        except ObjectDoesNotExist as exc:
            raise NoSuchUsage(usage_key) from exc

        return component

    def _lookup_asset_url(self, block: XBlock, asset_path: str) -> str | None:  # pylint: disable=unused-argument
        """
        Return an absolute URL for the specified static asset file that may
        belong to this XBlock.

        e.g. if the XBlock settings have a field value like "/static/foo.png"
        then this method will be called with asset_path="foo.png" and should
        return a URL like https://cdn.none/xblock/f843u89789/static/foo.png

        If the asset file is not recognized, return None

        This is called by the XBlockRuntime superclass in the .runtime module.

        TODO: Implement as part of larger static asset effort.
        """
        return None
