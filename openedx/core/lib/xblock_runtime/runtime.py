import warnings

from django.utils.lru_cache import lru_cache
from xblock.core import XBlock, XBlockAside
from xblock.field_data import ReadOnlyFieldData, SplitFieldData
from xblock.fields import Scope, ScopeIds
from xblock.runtime import Runtime, IdReader, IdGenerator, NullI18nService, MemoryIdManager

from openedx.core.lib.xblock_utils import xblock_local_resource_url
from xmodule.errortracker import make_error_tracker
from xmodule.modulestore.inheritance import inheriting_field_data
from .blockstore_kvs import collect_parsed_fields
from .id_managers import OpaqueKeyReader
from .shims import RuntimeShim, XBlockShim



class XBlockRuntime(RuntimeShim, Runtime):
    """
    This class manages one or more instantiated XBlocks for a particular user,
    providing those XBlocks with the standard XBlock runtime API (and some
    Open edX-specific additions) so that it can interact with the platform,
    and the platform can interact with it.

    The main reason we cannot make the runtime a long-lived singleton is that
    the XBlock runtime API requires 'user_id' to be a property of the runtime,
    not an argument passed in when loading particular blocks.
    """
    def __init__(self, system, user_id):
        # type: (XBlockRuntimeSystem, int) -> None
        super(XBlockRuntime, self).__init__(
            id_reader=system.id_reader,
            mixins=(
                XBlockShim,
            ),
            services={
                "i18n": NullI18nService(),
            },
            default_class=None,
            select=None,
            id_generator=system.id_generator,
        )
        self.system = system
        self.user_id = user_id

    def handler_url(self, block, handler_name, suffix='', query='', thirdparty=False):
        return system.handler_url(block, handler_name, suffix, query, thirdparty)

    def resource_url(self, resource):
        raise NotImplementedError("resource_url is not supported by Open edX.")

    def local_resource_url(self, block, uri):
        return xblock_local_resource_url(block, uri)

    def publish(self, block, event_type, event_data):
        if block.scope_ids.user_id != self.user_id:
            raise ValueError("XBlocks are not allowed to publish events for other users.")  # Is that true?
        pass  # TODO: publish events properly

    def applicable_aside_types(self, block):
        """ Disable XBlock asides in this runtime """
        return []

    def parse_xml_file(self, fileobj, id_generator=None):
        # Deny access to the inherited method
        raise NotImplementedError("XML Serialization is only supported with BlockstoreXBlockRuntime")

    def add_node_as_child(self, block, node, id_generator=None):
         """
         Called by XBlock.parse_xml to treat a child node as a child block.
         """
         # Deny access to the inherited method
         raise NotImplementedError("XML Serialization is only supported with BlockstoreXBlockRuntime")

    def service(self, block, service_name):
        """
        Return a service, or None.
        Services are objects implementing arbitrary other interfaces.
        """
        # TODO: Do these declarations actually help with anything? Maybe this check should
        # be removed from here and from XBlock.runtime
        declaration = block.service_declaration(service_name)
        if declaration is None:
            raise NoSuchServiceError("Service {!r} was not requested.".format(service_name))
        # Special case handling for some services:
        service = self.system.get_service(block.scope_ids, service_name)
        if service is None:
            service = super(XBlockRuntime, self).service(block, service_name)
        return service

class XBlockRuntimeSystem(object):
    """
    This class is essentially a factory for XBlockRuntimes. This is a
    long-lived object which provides the behavior specific to the application
    that wants to use XBlocks. Unlike XBlockRuntime, a single instance of this
    class can be used with many different XBlocks, whereas each XBlock gets its
    own instance of XBlockRuntime.
    """
    def __init__(
        self,
        handler_url,  # type: (Callable[[XBlock, string, string, string, bool], string]
        authored_data_kvs,  # type: InheritanceKeyValueStore
        student_data_kvs,  # type: InheritanceKeyValueStore
        runtime_class,  # type: XBlockRuntime
    ):
        """
        args:
            handler_url: A method that implements the XBlock runtime
                handler_url interface.
            authored_data_kvs: An InheritanceKeyValueStore used to retrieve
                any fields with UserScope.NONE
            student_data_kvs: An InheritanceKeyValueStore used to retrieve
                any fields with UserScope.ONE or UserScope.ALL
        """
        self.handler_url = handler_url
        # TODO: new ID manager:
        self.id_reader = OpaqueKeyReader()
        self.id_generator = MemoryIdManager()  # We don't really use id_generator until we need to support asides
        self.runtime_class = runtime_class

        # Field data storage/retrieval:
        authored_data = inheriting_field_data(authored_data_kvs)
        student_data = student_data_kvs
        #if authored_data_readonly:
        #    authored_data = ReadOnlyFieldData(authored_data)

        self.field_data = SplitFieldData({
            Scope.content: authored_data,
            Scope.settings: authored_data,
            Scope.parent: authored_data,
            Scope.children: authored_data,
            Scope.user_state_summary: student_data,
            Scope.user_state: student_data,
            Scope.user_info: student_data,
            Scope.preferences: student_data,
        })

        self._error_trackers = {}

    def get_runtime(self, user_id):
        # type: (int) -> XBlockRuntime
        return self.runtime_class(self, user_id)

    def get_service(self, scope_ids, service_name):
        """
        Get a runtime service

        Runtime services may come from this XBlockRuntimeSystem,
        or if this method returns None, they may come from the
        XBlockRuntime.
        """
        if service_name == "field-data":
            return self.field_data
        if service_name == 'error_tracker':
            return self.get_error_tracker_for_context(scope_ids.usage_id.context_key)
        return None  # None means see if XBlockRuntime offers this service

    @lru_cache(maxsize=32)
    def get_error_tracker_for_context(self, context_key):
        """
        Get an error tracker for the specified context.
        lru_cache makes this error tracker long-lived, for
        up to 32 contexts that have most recently been used.
        """
        return make_error_tracker()
