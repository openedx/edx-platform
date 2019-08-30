"""
Common base classes for all new XBlock runtimes.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import logging

from django.utils.lru_cache import lru_cache
from six.moves.urllib.parse import urljoin  # pylint: disable=import-error
from xblock.exceptions import NoSuchServiceError
from xblock.field_data import SplitFieldData
from xblock.fields import Scope
from xblock.runtime import Runtime, NullI18nService, MemoryIdManager
from web_fragments.fragment import Fragment

from openedx.core.djangoapps.xblock.apps import get_xblock_app_config
from openedx.core.lib.xblock_utils import xblock_local_resource_url
from xmodule.errortracker import make_error_tracker
from .id_managers import OpaqueKeyReader
from .shims import RuntimeShim, XBlockShim


log = logging.getLogger(__name__)


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

    # ** Do not add any XModule compatibility code to this class **
    # Add it to RuntimeShim instead, to help keep legacy code isolated.

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
        """
        Get the URL to a specific handler.
        """
        url = self.system.handler_url(
            usage_key=block.scope_ids.usage_id,
            handler_name=handler_name,
            user_id=XBlockRuntimeSystem.ANONYMOUS_USER if thirdparty else self.user_id,
        )
        if suffix:
            if not url.endswith('/'):
                url += '/'
            url += suffix
        if query:
            url += '&' if '?' in url else '?'
            url += query
        return url

    def resource_url(self, resource):
        raise NotImplementedError("resource_url is not supported by Open edX.")

    def local_resource_url(self, block, uri):
        """
        Get the absolute URL to a resource file (like a CSS/JS file or an image)
        that is part of an XBlock's python module.
        """
        relative_url = xblock_local_resource_url(block, uri)
        site_root_url = get_xblock_app_config().get_site_root_url()
        absolute_url = urljoin(site_root_url, relative_url)
        return absolute_url

    def publish(self, block, event_type, event_data):
        # TODO: publish events properly
        log.info("XBlock %s has published a '%s' event.", block.scope_ids.usage_id, event_type)

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

    def render(self, block, view_name, context=None):
        """
        Render a specific view of an XBlock.
        """
        # We only need to override this method because some XBlocks in the
        # edx-platform codebase use methods like add_webpack_to_fragment()
        # which create relative URLs (/static/studio/bundles/webpack-foo.js).
        # We want all resource URLs to be absolute, such as is done when
        # local_resource_url() is used.
        fragment = super(XBlockRuntime, self).render(block, view_name, context)
        needs_fix = False
        for resource in fragment.resources:
            if resource.kind == 'url' and resource.data.startswith('/'):
                needs_fix = True
                break
        if needs_fix:
            log.warning("XBlock %s returned relative resource URLs, which are deprecated", block.scope_ids.usage_id)
            # The Fragment API is mostly immutable, so changing a resource requires this:
            frag_data = fragment.to_dict()
            for resource in frag_data['resources']:
                if resource['kind'] == 'url' and resource['data'].startswith('/'):
                    log.debug("-> Relative resource URL: %s", resource['data'])
                    resource['data'] = get_xblock_app_config().get_site_root_url() + resource['data']
            fragment = Fragment.from_dict(frag_data)
        return fragment


class XBlockRuntimeSystem(object):
    """
    This class is essentially a factory for XBlockRuntimes. This is a
    long-lived object which provides the behavior specific to the application
    that wants to use XBlocks. Unlike XBlockRuntime, a single instance of this
    class can be used with many different XBlocks, whereas each XBlock gets its
    own instance of XBlockRuntime.
    """
    ANONYMOUS_USER = 'anon'  # Special value passed to handler_url() methods

    def __init__(
        self,
        handler_url,  # type: (Callable[[UsageKey, str, Union[int, ANONYMOUS_USER]], str]
        authored_data_store,  # type: FieldData
        student_data_store,  # type: FieldData
        runtime_class,  # type: XBlockRuntime
    ):
        """
        args:
            handler_url: A method to get URLs to call XBlock handlers. It must
                implement this signature:
                handler_url(
                    usage_key: UsageKey,
                    handler_name: str,
                    user_id: Union[int, ANONYMOUS_USER],
                )
                If user_id is ANONYMOUS_USER, the handler should execute without
                any user-scoped fields.
            authored_data_store: A FieldData instance used to retrieve/write
                any fields with UserScope.NONE
            student_data_store: A FieldData instance used to retrieve/write
                any fields with UserScope.ONE or UserScope.ALL
        """
        self.handler_url = handler_url
        self.id_reader = OpaqueKeyReader()
        self.id_generator = MemoryIdManager()  # We don't really use id_generator until we need to support asides
        self.runtime_class = runtime_class
        self.authored_data_store = authored_data_store
        self.field_data = SplitFieldData({
            Scope.content: authored_data_store,
            Scope.settings: authored_data_store,
            Scope.parent: authored_data_store,
            Scope.children: authored_data_store,
            Scope.user_state_summary: student_data_store,
            Scope.user_state: student_data_store,
            Scope.user_info: student_data_store,
            Scope.preferences: student_data_store,
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
    def get_error_tracker_for_context(self, context_key):  # pylint: disable=unused-argument
        """
        Get an error tracker for the specified context.
        lru_cache makes this error tracker long-lived, for
        up to 32 contexts that have most recently been used.
        """
        return make_error_tracker()
