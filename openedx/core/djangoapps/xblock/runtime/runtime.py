"""
Common base classes for all new XBlock runtimes.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import logging

from django.contrib.auth import get_user_model
from django.utils.lru_cache import lru_cache
from six.moves.urllib.parse import urljoin  # pylint: disable=import-error
from xblock.exceptions import NoSuchServiceError
from xblock.field_data import SplitFieldData
from xblock.fields import Scope
from xblock.runtime import DictKeyValueStore, KvsFieldData, NullI18nService, MemoryIdManager, Runtime
from web_fragments.fragment import Fragment

from courseware.model_data import DjangoKeyValueStore, FieldDataCache
from openedx.core.djangoapps.xblock.apps import get_xblock_app_config
from openedx.core.djangoapps.xblock.runtime.blockstore_field_data import BlockstoreFieldData
from openedx.core.djangoapps.xblock.runtime.mixin import LmsBlockMixin
from openedx.core.lib.xblock_utils import xblock_local_resource_url
from xmodule.errortracker import make_error_tracker
from .id_managers import OpaqueKeyReader
from .shims import RuntimeShim, XBlockShim


log = logging.getLogger(__name__)
User = get_user_model()


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

    def __init__(self, system, user):
        super(XBlockRuntime, self).__init__(
            id_reader=system.id_reader,
            mixins=(
                LmsBlockMixin,  # Adds Non-deprecated LMS/Studio functionality
                XBlockShim,  # Adds deprecated LMS/Studio functionality / backwards compatibility
            ),
            services={
                "i18n": NullI18nService(),
            },
            default_class=None,
            select=None,
            id_generator=system.id_generator,
        )
        self.system = system
        self.user = user
        self.user_id = user.id if self.user else None  # Must be set as a separate attribute since base class sets it
        self.block_field_datas = {}  # dict of FieldData stores for our loaded XBlocks. Key is the block's scope_ids.
        self.django_field_data_caches = {}  # dict of FieldDataCache objects for XBlock with database-based user state

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
        # Most common service is field-data so check that first:
        if service_name == "field-data":
            if block.scope_ids not in self.block_field_datas:
                try:
                    self.block_field_datas[block.scope_ids] = self._init_field_data_for_block(block)
                except:
                    # Don't try again pointlessly every time another field is accessed
                    self.block_field_datas[block.scope_ids] = None
                    raise
            return self.block_field_datas[block.scope_ids]
        # Check if the XBlockRuntimeSystem wants to handle this:
        service = self.system.get_service(block, service_name)
        # Otherwise, fall back to the base implementation which loads services
        # defined in the constructor:
        if service is None:
            service = super(XBlockRuntime, self).service(block, service_name)
        return service

    def _init_field_data_for_block(self, block):
        """
        Initialize the FieldData implementation for the specified XBlock
        """
        if self.user is None:
            # No user is specified, so we want to throw an error if anything attempts to read/write user-specific fields
            student_data_store = None
        elif self.user.is_anonymous:
            # The user is anonymous. Future work will support saving their state
            # in a cache or the django session but for now just use a highly
            # ephemeral dict.
            student_data_store = KvsFieldData(kvs=DictKeyValueStore())
        elif self.system.student_data_mode == XBlockRuntimeSystem.STUDENT_DATA_EPHEMERAL:
            # We're in an environment like Studio where we want to let the
            # author test blocks out but not permanently save their state.
            # This in-memory dict will typically only persist for one
            # request-response cycle, so we need to soon replace it with a store
            # that puts the state into a cache or the django session.
            student_data_store = KvsFieldData(kvs=DictKeyValueStore())
        else:
            # Use database-backed field data (i.e. store user_state in StudentModule)
            context_key = block.scope_ids.usage_id.context_key
            if context_key not in self.django_field_data_caches:
                field_data_cache = FieldDataCache(
                    [block], course_id=context_key, user=self.user, asides=None, read_only=False,
                )
                self.django_field_data_caches[context_key] = field_data_cache
            else:
                field_data_cache = self.django_field_data_caches[context_key]
                field_data_cache.add_descriptors_to_cache([block])
            student_data_store = KvsFieldData(kvs=DjangoKeyValueStore(field_data_cache))

        return SplitFieldData({
            Scope.content: self.system.authored_data_store,
            Scope.settings: self.system.authored_data_store,
            Scope.parent: self.system.authored_data_store,
            Scope.children: self.system.authored_data_store,
            Scope.user_state_summary: student_data_store,
            Scope.user_state: student_data_store,
            Scope.user_info: student_data_store,
            Scope.preferences: student_data_store,
        })

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

    STUDENT_DATA_EPHEMERAL = 'ephemeral'
    STUDENT_DATA_PERSISTED = 'persisted'

    def __init__(
        self,
        handler_url,  # type: (Callable[[UsageKey, str, Union[int, ANONYMOUS_USER]], str]
        student_data_mode,  # type: Union[STUDENT_DATA_EPHEMERAL, STUDENT_DATA_PERSISTED]
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
            student_data_mode: Specifies whether student data should be kept
                in a temporary in-memory store (e.g. Studio) or persisted
                forever in the database.
            runtime_class: What runtime to use, e.g. BlockstoreXBlockRuntime
        """
        self.handler_url = handler_url
        self.id_reader = OpaqueKeyReader()
        self.id_generator = MemoryIdManager()  # We don't really use id_generator until we need to support asides
        self.runtime_class = runtime_class
        self.authored_data_store = BlockstoreFieldData()
        assert student_data_mode in (self.STUDENT_DATA_EPHEMERAL, self.STUDENT_DATA_PERSISTED)
        self.student_data_mode = student_data_mode
        self._error_trackers = {}

    def get_runtime(self, user):
        """
        Get the XBlock runtime for the specified Django user. The user can be
        a regular user, an AnonymousUser, or None.
        """
        return self.runtime_class(self, user)

    def get_service(self, block, service_name):
        """
        Get a runtime service

        Runtime services may come from this XBlockRuntimeSystem,
        or if this method returns None, they may come from the
        XBlockRuntime.
        """
        if service_name == 'error_tracker':
            return self.get_error_tracker_for_context(block.scope_ids.usage_id.context_key)
        return None  # None means see if XBlockRuntime offers this service

    @lru_cache(maxsize=32)
    def get_error_tracker_for_context(self, context_key):  # pylint: disable=unused-argument
        """
        Get an error tracker for the specified context.
        lru_cache makes this error tracker long-lived, for
        up to 32 contexts that have most recently been used.
        """
        return make_error_tracker()
