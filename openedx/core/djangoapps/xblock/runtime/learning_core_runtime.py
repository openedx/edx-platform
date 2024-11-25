"""
Learning Core XBlock Runtime code
"""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone

<<<<<<< HEAD
from django.core.exceptions import ObjectDoesNotExist
from django.db.transaction import atomic

from openedx_learning.core.components import api as components_api
from openedx_learning.core.contents import api as contents_api
from openedx_learning.core.publishing import api as publishing_api
=======
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.transaction import atomic
from django.urls import reverse

from openedx_learning.api import authoring as authoring_api
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

from lxml import etree

from xblock.core import XBlock
from xblock.exceptions import NoSuchUsage
from xblock.fields import Field, Scope, ScopeIds
from xblock.field_data import FieldData

<<<<<<< HEAD
from openedx.core.lib.xblock_serializer.api import serialize_modulestore_block_for_blockstore
=======
from openedx.core.djangoapps.xblock.api import get_xblock_app_config
from openedx.core.lib.xblock_serializer.api import serialize_modulestore_block_for_learning_core
from openedx.core.lib.xblock_serializer.data import StaticFile
from ..data import AuthoredDataMode, LatestVersion
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
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

<<<<<<< HEAD
    def get_block(self, usage_key, for_parent=None):
=======
    def get_block(self, usage_key, for_parent=None, *, version: int | LatestVersion = LatestVersion.AUTO):
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
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
<<<<<<< HEAD
        # TODO: For now, this runtime will only be used in CMS, so it's fine to just return the Draft version.
        #       However, we will need the runtime to return the Published version for LMS (and Draft for LMS-Preview).
        #       We should base this Draft vs Published decision on a runtime initialization parameter.
        component_version = component.versioning.draft
=======

        if version == LatestVersion.AUTO:
            if self.authored_data_mode == AuthoredDataMode.DEFAULT_DRAFT:
                version = LatestVersion.DRAFT
            else:
                version = LatestVersion.PUBLISHED
        if self.authored_data_mode == AuthoredDataMode.STRICTLY_PUBLISHED and version != LatestVersion.PUBLISHED:
            raise ValidationError("This runtime only allows accessing the published version of components")
        if version == LatestVersion.DRAFT:
            component_version = component.versioning.draft
        elif version == LatestVersion.PUBLISHED:
            component_version = component.versioning.published
        else:
            assert isinstance(version, int)
            component_version = component.versioning.version_num(version)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
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

<<<<<<< HEAD
=======
        # Store the version request on the block so we can retrieve it when needed for generating handler URLs etc.
        block._runtime_requested_version = version  # pylint: disable=protected-access

>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        # Update field data with parsed values. We can't call .save() because it will call save_block(), below.
        block.force_save_fields(block._get_fields_to_save())  # pylint: disable=protected-access

        # We've pre-loaded the fields for this block, so the FieldData shouldn't
        # consider these values "changed" in its sense of "you have to persist
        # these because we've altered the field values from what was stored".
<<<<<<< HEAD
        self.system.authored_data_store.mark_unchanged(block)

        return block

=======
        self.authored_data_store.mark_unchanged(block)

        return block

    def get_block_assets(self, block, fetch_asset_data):
        """
        Return a list of StaticFile entries.

        If ``fetch_data`` is True, we will read the actual asset file data from
        storage and return it as part of the ``StaticFiles``. This is expensive,
        and not necessary for something like writing a new version of the OLX in
        response to a "Save" in the editor. But it is necessary for something
        like serializing to the clipboard, where we make full copies of the
        assets.

        TODO: When we want to copy a whole Section at a time, doing these
        lookups one by one is going to get slow. At some point we're going to
        want something to look up a bunch of blocks at once.
        """
        component_version = self._get_component_version_from_block(block)

        # cvc = the ComponentVersionContent through-table
        cvc_list = (
            component_version
            .componentversioncontent_set
            .filter(content__has_file=True)
            .select_related('content')
            .order_by('key')
        )

        return [
            StaticFile(
                name=cvc.key,
                url=self._absolute_url_for_asset(component_version, cvc.key),
                data=cvc.content.read_file().read() if fetch_asset_data else None,
            )
            for cvc in cvc_list
        ]

>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    def save_block(self, block):
        """
        Save any pending field data values to Learning Core data models.

        This gets called by block.save() - do not call this directly.
        """
<<<<<<< HEAD
        if not self.system.authored_data_store.has_changes(block):
            return  # No changes, so no action needed.

=======
        if not self.authored_data_store.has_changes(block):
            return  # No changes, so no action needed.

        if block._runtime_requested_version != LatestVersion.DRAFT:  # pylint: disable=protected-access
            # Not sure if this is an important restriction but it seems like overwriting the latest version based on
            # an old version is likely an accident, so for now we're not going to allow it.
            raise ValidationError(
                "Do not make changes to a component starting from the published or past versions. Use the latest draft."
            )

>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        # Verify that the user has permission to write to authored data in this
        # learning context:
        if self.user is not None:
            learning_context = get_learning_context_impl(block.scope_ids.usage_id)
            if not learning_context.can_edit_block(self.user, block.scope_ids.usage_id):
                log.warning("User %s does not have permission to edit %s", self.user.username, block.scope_ids.usage_id)
                raise RuntimeError("You do not have permission to edit this XBlock")

<<<<<<< HEAD
        # We need Blockstore's serialization so we don't have `url_name` showing
        # up in all the OLX. TODO: Rename this later, after we figure out what
        # other changes we need to make in the serialization as part of the
        # Blockstore -> Learning Core conversion.
        serialized = serialize_modulestore_block_for_blockstore(block)
=======
        serialized = serialize_modulestore_block_for_learning_core(block)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        now = datetime.now(tz=timezone.utc)
        usage_key = block.scope_ids.usage_id
        with atomic():
            component = self._get_component_from_usage_key(usage_key)
<<<<<<< HEAD
            block_media_type = contents_api.get_or_create_media_type(
                f"application/vnd.openedx.xblock.v1.{usage_key.block_type}+xml"
            )
            content = contents_api.get_or_create_text_content(
=======
            block_media_type = authoring_api.get_or_create_media_type(
                f"application/vnd.openedx.xblock.v1.{usage_key.block_type}+xml"
            )
            content = authoring_api.get_or_create_text_content(
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
                component.learning_package_id,
                block_media_type.id,
                text=serialized.olx_str,
                created=now,
            )
<<<<<<< HEAD
            components_api.create_next_version(
=======
            authoring_api.create_next_version(
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
                component.pk,
                title=block.display_name,
                content_to_replace={
                    "block.xml": content.id,
                },
                created=now,
            )
<<<<<<< HEAD
        self.system.authored_data_store.mark_unchanged(block)
=======
        self.authored_data_store.mark_unchanged(block)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    def _get_component_from_usage_key(self, usage_key):
        """
        Note that Components aren't ever really truly deleted, so this will
        return a Component if this usage key has ever been used, even if it was
        later deleted.

        TODO: This is the third place where we're implementing this. Figure out
        where the definitive place should be and have everything else call that.
        """
<<<<<<< HEAD
        learning_package = publishing_api.get_learning_package_by_key(str(usage_key.lib_key))
        try:
            component = components_api.get_component_by_key(
=======
        learning_package = authoring_api.get_learning_package_by_key(str(usage_key.lib_key))
        try:
            component = authoring_api.get_component_by_key(
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
                learning_package.id,
                namespace='xblock.v1',
                type_name=usage_key.block_type,
                local_key=usage_key.block_id,
            )
        except ObjectDoesNotExist as exc:
            raise NoSuchUsage(usage_key) from exc

        return component

<<<<<<< HEAD
    def _lookup_asset_url(self, block: XBlock, asset_path: str) -> str | None:  # pylint: disable=unused-argument
=======
    def _get_component_version_from_block(self, block):
        """
        Given an XBlock instance, return the Learning Core ComponentVersion.

        This relies on our runtime setting the _runtime_requested_version
        attribute on blocks that it fetches.
        """
        usage_key = block.usage_key
        component = self._get_component_from_usage_key(usage_key)

        block_version = block._runtime_requested_version  # pylint: disable=protected-access
        if block_version == LatestVersion.DRAFT:
            component_version = component.versioning.draft
        elif block_version == LatestVersion.PUBLISHED:
            component_version = component.versioning.published
        else:
            component_version = component.versioning.version_num(block_version)

        return component_version

    def _absolute_url_for_asset(self, component_version, asset_path):
        """
        The full URL for a specific library asset in a ComponentVersion.

        This does not check for whether the path actually exists–it just returns
        where it would be if it did exist.
        """
        # This function should return absolute URLs, so we need the site root.
        site_root_url = get_xblock_app_config().get_site_root_url()

        return site_root_url + reverse(
            'content_libraries:library-assets',
            kwargs={
                'component_version_uuid': component_version.uuid,
                'asset_path': f"static/{asset_path}",
            }
        )

    def _lookup_asset_url(self, block: XBlock, asset_path: str) -> str | None:
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        """
        Return an absolute URL for the specified static asset file that may
        belong to this XBlock.

<<<<<<< HEAD
        e.g. if the XBlock settings have a field value like "/static/foo.png"
        then this method will be called with asset_path="foo.png" and should
        return a URL like https://cdn.none/xblock/f843u89789/static/foo.png
=======
        e.g. if the XBlock settings have a field value like "/static/test.png"
        then this method will be called with asset_path="test.png" and should
        return a URL like:

          http://studio.local.openedx.io:8001/library_assets/component_versions/cd31871e-a342-4c3f-ba2f-a661bf630996/static/test.png
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

        If the asset file is not recognized, return None

        This is called by the XBlockRuntime superclass in the .runtime module.

<<<<<<< HEAD
        TODO: Implement as part of larger static asset effort.
        """
        return None
=======
        Implementation Details
        ----------------------
        The standard XBlock "static/{asset_path}" substitution strips out the
        leading "static/" part because it assumes that all files will exist in a
        shared, flat namespace (i.e. a course's Files and Uploads).

        Learning Core treats assets differently. Each Component has its own,
        isolated namespace for asset storage. Furthermore, that namespace
        contains content that are not meant to be downloadable, like the
        block.xml (the OLX of the Component). There may one day be other files
        that are not meant to be externally downloadable there as well, like
        Markdown or LaTeX source files or grader code.

        By convention, the static assets that we store in Learning Core and are
        meant for download sit inside a static/ directory that is local to each
        Component (and actually separate for each Component Version).

        So the transformation looks like this:

        1. The Learning Core ComponentVersion has an asset stored as
           ``static/test.png`` in the database.
        2. The original OLX content we store references ``/static/test.png``,
           per OLX convention. Note the leading "/".
        3. The ReplaceURLService XBlock runtime service invokes
           ``static_replace`` and strips out ``/static/``.
        4. The method we're in now is invoked with a ``static_path`` of just
           ``test.png``, because that's the transformation that works for
           ModuleStore-based courses, where everything is stored in the root of
           a shared Files and Uploads space.
        5. This method then builds a URL that re-adds the "static/" prefix, and
           then points to the ComponentVersion-specific location for that asset.

        Note: This means that the URL for a static asset will change with every
        new version of the Component that is created, i.e. with every edit
        that's saved–even if the asset itself doesn't change. This was the
        tradeoff we made in order to put each version's assets in an isolated
        space, and to make sure that we don't break things like relative links.
        On the backend, we only store the asset once.

        Performance Note
        ----------------
        This can theoretically get very expensive if there are many, many static
        asset references in a Component. It's also very cacheable–we could put
        it in a RequestCache with a key of (usage_key, version_num), and have
        the value be the component_version.uuid and the full list of assets. I'm
        not doing this yet in order to keep the code simpler, but I'm leaving
        this note here in case someone needs to optimize this later.
        """
        component_version = self._get_component_version_from_block(block)

        try:
            content = (
                component_version
                .componentversioncontent_set
                .filter(content__has_file=True)
                .get(key=f"static/{asset_path}")
            )
        except ObjectDoesNotExist:
            # This means we see a path that _looks_ like it should be a static
            # asset for this Component, but that static asset doesn't really
            # exist.
            return None

        return self._absolute_url_for_asset(component_version, asset_path)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
