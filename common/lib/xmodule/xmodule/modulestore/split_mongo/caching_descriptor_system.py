import sys
import logging

from contracts import contract, new_contract
from fs.osfs import OSFS
from lazy import lazy
from xblock.runtime import KvsFieldData, KeyValueStore
from xblock.fields import ScopeIds
from xblock.core import XBlock
from opaque_keys.edx.locator import BlockUsageLocator, LocalId, CourseLocator, LibraryLocator, DefinitionLocator

from xmodule.library_tools import LibraryToolsService
from xmodule.mako_module import MakoDescriptorSystem
from xmodule.error_module import ErrorDescriptor
from xmodule.errortracker import exc_info_to_str
from xmodule.modulestore import BlockData
from xmodule.modulestore.edit_info import EditInfoRuntimeMixin
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.inheritance import inheriting_field_data, InheritanceMixin
from xmodule.modulestore.split_mongo import BlockKey, CourseEnvelope
from xmodule.modulestore.split_mongo.id_manager import SplitMongoIdManager
from xmodule.modulestore.split_mongo.definition_lazy_loader import DefinitionLazyLoader
from xmodule.modulestore.split_mongo.split_mongo_kvs import SplitMongoKVS
from xmodule.x_module import XModuleMixin

log = logging.getLogger(__name__)

new_contract('BlockUsageLocator', BlockUsageLocator)
new_contract('CourseLocator', CourseLocator)
new_contract('LibraryLocator', LibraryLocator)
new_contract('BlockKey', BlockKey)
new_contract('BlockData', BlockData)
new_contract('CourseEnvelope', CourseEnvelope)
new_contract('XBlock', XBlock)


class CachingDescriptorSystem(MakoDescriptorSystem, EditInfoRuntimeMixin):
    """
    A system that has a cache of a course version's json that it will use to load modules
    from, with a backup of calling to the underlying modulestore for more data.

    Computes the settings (nee 'metadata') inheritance upon creation.
    """
    @contract(course_entry=CourseEnvelope)
    def __init__(self, modulestore, course_entry, default_class, module_data, lazy, **kwargs):
        """
        Computes the settings inheritance and sets up the cache.

        modulestore: the module store that can be used to retrieve additional
        modules

        course_entry: the originally fetched enveloped course_structure w/ branch and course id info.
        Callers to _load_item provide an override but that function ignores the provided structure and
        only looks at the branch and course id

        module_data: a dict mapping Location -> json that was cached from the
            underlying modulestore
        """
        # needed by capa_problem (as runtime.filestore via this.resources_fs)
        if course_entry.course_key.course:
            root = modulestore.fs_root / course_entry.course_key.org / course_entry.course_key.course / course_entry.course_key.run
        else:
            root = modulestore.fs_root / str(course_entry.structure['_id'])
        root.makedirs_p()  # create directory if it doesn't exist

        id_manager = SplitMongoIdManager(self)
        kwargs.setdefault('id_reader', id_manager)
        kwargs.setdefault('id_generator', id_manager)

        super(CachingDescriptorSystem, self).__init__(
            field_data=None,
            load_item=self._load_item,
            resources_fs=OSFS(root),
            **kwargs
        )
        self.modulestore = modulestore
        self.course_entry = course_entry
        # set course_id attribute to avoid problems with subsystems that expect
        # it here. (grading, for example)
        self.course_id = course_entry.course_key
        self.lazy = lazy
        self.module_data = module_data
        self.default_class = default_class
        self.local_modules = {}
        self._services['library_tools'] = LibraryToolsService(modulestore)

    @lazy
    @contract(returns="dict(BlockKey: BlockKey)")
    def _parent_map(self):
        parent_map = {}
        for block_key, block in self.course_entry.structure['blocks'].iteritems():
            for child in block.fields.get('children', []):
                parent_map[child] = block_key
        return parent_map

    @contract(usage_key="BlockUsageLocator | BlockKey", course_entry_override="CourseEnvelope | None")
    def _load_item(self, usage_key, course_entry_override=None, **kwargs):
        """
        Instantiate the xblock fetching it either from the cache or from the structure

        :param course_entry_override: the course_info with the course_key to use (defaults to cached)
        """
        # usage_key is either a UsageKey or just the block_key. if a usage_key,
        if isinstance(usage_key, BlockUsageLocator):

            # trust the passed in key to know the caller's expectations of which fields are filled in.
            # particularly useful for strip_keys so may go away when we're version aware
            course_key = usage_key.course_key

            if isinstance(usage_key.block_id, LocalId):
                try:
                    return self.local_modules[usage_key]
                except KeyError:
                    raise ItemNotFoundError
            else:
                block_key = BlockKey.from_usage_key(usage_key)
                version_guid = self.course_entry.course_key.version_guid
        else:
            block_key = usage_key

            course_info = course_entry_override or self.course_entry
            course_key = course_info.course_key
            version_guid = course_key.version_guid

        # look in cache
        cached_module = self.modulestore.get_cached_block(course_key, version_guid, block_key)
        if cached_module:
            return cached_module

        block_data = self.get_module_data(block_key, course_key)

        class_ = self.load_block_type(block_data.block_type)
        block = self.xblock_from_json(class_, course_key, block_key, block_data, course_entry_override, **kwargs)

        # TODO Once PLAT-1055 is implemented, we can expose the course version
        # information within the key identifier of the block.  Until then, set
        # the course_version as a field on the returned block so higher layers
        # can use it when needed.
        block.course_version = version_guid

        self.modulestore.cache_block(course_key, version_guid, block_key, block)
        return block

    @contract(block_key=BlockKey, course_key="CourseLocator | LibraryLocator")
    def get_module_data(self, block_key, course_key):
        """
        Get block from module_data adding it to module_data if it's not already there but is in the structure

        Raises:
            ItemNotFoundError if block is not in the structure
        """
        json_data = self.module_data.get(block_key)
        if json_data is None:
            # deeper than initial descendant fetch or doesn't exist
            self.modulestore.cache_items(self, [block_key], course_key, lazy=self.lazy)
            json_data = self.module_data.get(block_key)
            if json_data is None:
                raise ItemNotFoundError(block_key)

        return json_data

    # xblock's runtime does not always pass enough contextual information to figure out
    # which named container (course x branch) or which parent is requesting an item. Because split allows
    # a many:1 mapping from named containers to structures and because item's identities encode
    # context as well as unique identity, this function must sometimes infer whether the access is
    # within an unspecified named container. In most cases, course_entry_override will give the
    # explicit context; however, runtime.get_block(), e.g., does not. HOWEVER, there are simple heuristics
    # which will work 99.999% of the time: a runtime is thread & even context specific. The likelihood that
    # the thread is working with more than one named container pointing to the same specific structure is
    # low; thus, the course_entry is most likely correct. If the thread is looking at > 1 named container
    # pointing to the same structure, the access is likely to be chunky enough that the last known container
    # is the intended one when not given a course_entry_override; thus, the caching of the last branch/course id.
    @contract(block_key="BlockKey | None")
    def xblock_from_json(self, class_, course_key, block_key, block_data, course_entry_override=None, **kwargs):
        """
        Load and return block info.
        """
        if course_entry_override is None:
            course_entry_override = self.course_entry
        else:
            # most recent retrieval is most likely the right one for next caller (see comment above fn)
            self.course_entry = CourseEnvelope(course_entry_override.course_key, self.course_entry.structure)

        definition_id = block_data.definition

        # If no usage id is provided, generate an in-memory id
        if block_key is None:
            block_key = BlockKey(block_data.block_type, LocalId())

        convert_fields = lambda field: self.modulestore.convert_references_to_keys(
            course_key, class_, field, self.course_entry.structure['blocks'],
        )

        if definition_id is not None and not block_data.definition_loaded:
            definition_loader = DefinitionLazyLoader(
                self.modulestore,
                course_key,
                block_key.type,
                definition_id,
                convert_fields,
            )
        else:
            definition_loader = None

        # If no definition id is provide, generate an in-memory id
        if definition_id is None:
            definition_id = LocalId()

        # Construct the Block Usage Locator:
        block_locator = course_key.make_usage_key(
            block_type=block_key.type,
            block_id=block_key.id,
        )

        converted_fields = convert_fields(block_data.fields)
        converted_defaults = convert_fields(block_data.defaults)
        if block_key in self._parent_map:
            parent_key = self._parent_map[block_key]
            parent = course_key.make_usage_key(parent_key.type, parent_key.id)
        else:
            parent = None

        aside_fields = None

        # for the situation if block_data has no asides attribute
        # (in case it was taken from memcache)
        try:
            if block_data.asides:
                aside_fields = {block_key.type: {}}
                for aside in block_data.asides:
                    aside_fields[block_key.type].update(aside['fields'])
        except AttributeError:
            pass

        try:
            kvs = SplitMongoKVS(
                definition_loader,
                converted_fields,
                converted_defaults,
                parent=parent,
                aside_fields=aside_fields,
                field_decorator=kwargs.get('field_decorator')
            )

            if InheritanceMixin in self.modulestore.xblock_mixins:
                field_data = inheriting_field_data(kvs)
            else:
                field_data = KvsFieldData(kvs)

            module = self.construct_xblock_from_class(
                class_,
                ScopeIds(None, block_key.type, definition_id, block_locator),
                field_data,
                for_parent=kwargs.get('for_parent')
            )
        except Exception:  # pylint: disable=broad-except
            log.warning("Failed to load descriptor", exc_info=True)
            return ErrorDescriptor.from_json(
                block_data,
                self,
                course_entry_override.course_key.make_usage_key(
                    block_type='error',
                    block_id=block_key.id
                ),
                error_msg=exc_info_to_str(sys.exc_info())
            )

        edit_info = block_data.edit_info
        module._edited_by = edit_info.edited_by  # pylint: disable=protected-access
        module._edited_on = edit_info.edited_on  # pylint: disable=protected-access
        module.previous_version = edit_info.previous_version
        module.update_version = edit_info.update_version
        module.source_version = edit_info.source_version
        module.definition_locator = DefinitionLocator(block_key.type, definition_id)

        for wrapper in self.modulestore.xblock_field_data_wrappers:
            module._field_data = wrapper(module, module._field_data)  # pylint: disable=protected-access

        # decache any pending field settings
        module.save()

        # If this is an in-memory block, store it in this system
        if isinstance(block_locator.block_id, LocalId):
            self.local_modules[block_locator] = module

        return module

    def get_edited_by(self, xblock):
        """
        See :meth: cms.lib.xblock.runtime.EditInfoRuntimeMixin.get_edited_by
        """
        return xblock._edited_by

    def get_edited_on(self, xblock):
        """
        See :class: cms.lib.xblock.runtime.EditInfoRuntimeMixin
        """
        return xblock._edited_on

    @contract(xblock='XBlock')
    def get_subtree_edited_by(self, xblock):
        """
        See :class: cms.lib.xblock.runtime.EditInfoRuntimeMixin
        """
        # pylint: disable=protected-access
        if not hasattr(xblock, '_subtree_edited_by'):
            block_data = self.module_data[BlockKey.from_usage_key(xblock.location)]
            if block_data.edit_info._subtree_edited_by is None:
                self._compute_subtree_edited_internal(
                    block_data, xblock.location.course_key
                )
            xblock._subtree_edited_by = block_data.edit_info._subtree_edited_by

        return xblock._subtree_edited_by

    @contract(xblock='XBlock')
    def get_subtree_edited_on(self, xblock):
        """
        See :class: cms.lib.xblock.runtime.EditInfoRuntimeMixin
        """
        # pylint: disable=protected-access
        if not hasattr(xblock, '_subtree_edited_on'):
            block_data = self.module_data[BlockKey.from_usage_key(xblock.location)]
            if block_data.edit_info._subtree_edited_on is None:
                self._compute_subtree_edited_internal(
                    block_data, xblock.location.course_key
                )
            xblock._subtree_edited_on = block_data.edit_info._subtree_edited_on

        return xblock._subtree_edited_on

    def get_published_by(self, xblock):
        """
        See :class: cms.lib.xblock.runtime.EditInfoRuntimeMixin
        """
        if not hasattr(xblock, '_published_by'):
            self.modulestore.compute_published_info_internal(xblock)

        return getattr(xblock, '_published_by', None)

    def get_published_on(self, xblock):
        """
        See :class: cms.lib.xblock.runtime.EditInfoRuntimeMixin
        """
        if not hasattr(xblock, '_published_on'):
            self.modulestore.compute_published_info_internal(xblock)

        return getattr(xblock, '_published_on', None)

    @contract(block_data='BlockData')
    def _compute_subtree_edited_internal(self, block_data, course_key):
        """
        Recurse the subtree finding the max edited_on date and its corresponding edited_by. Cache it.
        """
        # pylint: disable=protected-access
        max_date = block_data.edit_info.edited_on
        max_date_by = block_data.edit_info.edited_by

        for child in block_data.fields.get('children', []):
            child_data = self.get_module_data(BlockKey(*child), course_key)
            if block_data.edit_info._subtree_edited_on is None:
                self._compute_subtree_edited_internal(child_data, course_key)
            if child_data.edit_info._subtree_edited_on > max_date:
                max_date = child_data.edit_info._subtree_edited_on
                max_date_by = child_data.edit_info._subtree_edited_by

        block_data.edit_info._subtree_edited_on = max_date
        block_data.edit_info._subtree_edited_by = max_date_by

    def get_aside_of_type(self, block, aside_type):
        """
        See `runtime.Runtime.get_aside_of_type`

        This override adds the field data from the block to the aside
        """
        asides_cached = block.get_asides() if isinstance(block, XModuleMixin) else None
        if asides_cached:
            for aside in asides_cached:
                if aside.scope_ids.block_type == aside_type:
                    return aside

        new_aside = super(CachingDescriptorSystem, self).get_aside_of_type(block, aside_type)
        new_aside._field_data = block._field_data  # pylint: disable=protected-access

        for key, _ in new_aside.fields.iteritems():
            if isinstance(key, KeyValueStore.Key) and block._field_data.has(new_aside, key):  # pylint: disable=protected-access
                try:
                    value = block._field_data.get(new_aside, key)  # pylint: disable=protected-access
                except KeyError:
                    pass
                else:
                    setattr(new_aside, key, value)

        block.add_aside(new_aside)
        return new_aside
