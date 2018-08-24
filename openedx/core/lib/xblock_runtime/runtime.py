from xblock.core import XBlock, XBlockAside
from xblock.field_data import ReadOnlyFieldData, SplitFieldData
from xblock.fields import Scope, ScopeIds
from xblock.runtime import Runtime, IdReader, IdGenerator, NullI18nService

from openedx.core.lib.xblock_utils import xblock_local_resource_url
from xmodule.modulestore.inheritance import inheriting_field_data
from .id_managers import OpaqueKeyReader, AsideKeyGenerator


class XBlockRuntime(Runtime):
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
            mixins=(),
            services={
                "field-data": system.field_data,
                "i18n": NullI18nService(),
            },
            default_class=None,
            select=None,
            id_generator=system.id_generator,
        )
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
        authored_data_readonly=True  # type: bool
    ):
        """
        args:
            handler_url: A method that implements the XBlock runtime
                handler_url interface.
            authored_data_kvs: An InheritanceKeyValueStore used to retrieve
                any fields with UserScope.NONE
            student_data_kvs: An InheritanceKeyValueStore used to retrieve
                any fields with UserScope.ONE or UserScope.ALL
            authored_data_readonly: If true, this runtime system will not allow
                XBlocks to write to any UserScope.NONE fields.
        """
        self.handler_url = handler_url
        self.id_reader = OpaqueKeyReader()
        self.id_generator = AsideKeyGenerator()

        # Field data storage/retrieval:
        authored_data = inheriting_field_data(authored_data_kvs)
        student_data = student_data_kvs
        if authored_data_readonly:
            authored_data = ReadOnlyFieldData(authored_data)

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

    def get_block(self, usage_id, user_id):
        # type: (UsageKey, int) -> XBlock
        runtime = XBlockRuntime(self, user_id)
        return runtime.get_block(usage_id)
