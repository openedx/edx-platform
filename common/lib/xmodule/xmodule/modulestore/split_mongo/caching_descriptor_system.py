import sys
import logging
from xmodule.mako_module import MakoDescriptorSystem
from xmodule.x_module import XModuleDescriptor
from xmodule.modulestore.locator import BlockUsageLocator
from xmodule.error_module import ErrorDescriptor
from xmodule.errortracker import exc_info_to_str
from xblock.runtime import DbModel
from ..exceptions import ItemNotFoundError
from .split_mongo_kvs import SplitMongoKVS, SplitMongoKVSid

log = logging.getLogger(__name__)

# TODO should this be here or w/ x_module or ???
class CachingDescriptorSystem(MakoDescriptorSystem):
    """
    A system that has a cache of a course version's json that it will use to load modules
    from, with a backup of calling to the underlying modulestore for more data.

    Computes the metadata inheritance upon creation.
    """
    def __init__(self, modulestore, course_entry, module_data, lazy,
        default_class, error_tracker, render_template):
        """
        Computes the metadata inheritance and sets up the cache.

        modulestore: the module store that can be used to retrieve additional
        modules

        module_data: a dict mapping Location -> json that was cached from the
            underlying modulestore

        default_class: The default_class to use when loading an
            XModuleDescriptor from the module_data

        resources_fs: a filesystem, as per MakoDescriptorSystem

        error_tracker: a function that logs errors for later display to users

        render_template: a function for rendering templates, as per
            MakoDescriptorSystem
        """
        # TODO find all references to resources_fs and make handle None
        super(CachingDescriptorSystem, self).__init__(
                self._load_item, None, error_tracker, render_template)
        self.modulestore = modulestore
        self.course_entry = course_entry
        self.lazy = lazy
        self.module_data = module_data
        self.default_class = default_class
        # TODO see if self.course_id is needed: is already in course_entry but could be > 1 value
        # Compute inheritance
        modulestore.inherit_metadata(course_entry.get('blocks', {}),
            course_entry.get('blocks', {})
            .get(course_entry.get('root')))

    def _load_item(self, usage_id):
        # TODO ensure all callers of system.load_item pass just the id
        json_data = self.module_data.get(usage_id)
        if json_data is None:
            # deeper than initial descendant fetch or doesn't exist
            self.modulestore.cache_items(self, [usage_id], lazy=self.lazy)
            json_data = self.module_data.get(usage_id)
            if json_data is None:
                raise ItemNotFoundError

        class_ = XModuleDescriptor.load_class(
            json_data.get('category'),
            self.default_class
        )
        return self.xblock_from_json(class_, usage_id, json_data)

    def xblock_from_json(self, class_, usage_id, json_data):
        try:
            # most likely a lazy loader but not the id directly
            definition = json_data.get('definition', {})
            metadata = json_data.get('metadata', {})

            kvs = SplitMongoKVS(definition,
                json_data.get('children', []),
                metadata, json_data.get('_inherited_metadata'))

            block_locator = BlockUsageLocator(
                version_guid=self.course_entry['_id'],
                usage_id=usage_id,
                course_id=self.course_entry.get('course_id'), 
                revision=self.course_entry.get('revision')
            )
            model_data = DbModel(kvs, class_, None,
                SplitMongoKVSid(
                    # DbModel req's that these support .url()
                    block_locator,
                    self.modulestore.definition_locator(definition)))
            module = class_(self, json_data.get('category'),
                block_locator, self.modulestore.definition_locator(definition),
                model_data)
            module.edited_by = json_data.get('edited_by')
            module.edited_on = json_data.get('edited_on')
            module.previous_version = json_data.get('previous_version')
            module.update_version = json_data.get('update_version')
            return module
        except:
            log.warning("Failed to load descriptor", exc_info=True)
            if usage_id is None:
                usage_id = "MISSING"

            return ErrorDescriptor.from_json(
                json_data,
                self,
                BlockUsageLocator(version_guid=self.course_entry['_id'],
                    usage_id=usage_id),
                error_msg=exc_info_to_str(sys.exc_info())
            )
