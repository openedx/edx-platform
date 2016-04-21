"""
Module implementing `xblock.runtime.Runtime` functionality for the LMS
"""
import re

from django.conf import settings
from django.core.urlresolvers import reverse

from badges.service import BadgingService
from badges.utils import badges_enabled
from openedx.core.djangoapps.user_api.course_tag import api as user_course_tag_api
from openedx.core.lib.xblock_utils import xblock_local_resource_url
from request_cache.middleware import RequestCache
import xblock.reference.plugins
from xmodule.library_tools import LibraryToolsService
from xmodule.modulestore.django import modulestore, ModuleI18nService
from xmodule.partitions.partitions_service import PartitionService
from xmodule.services import SettingsService
from xmodule.x_module import ModuleSystem

from lms.djangoapps.lms_xblock.models import XBlockAsidesConfig


def _quote_slashes(match):
    """
    Helper function for `quote_slashes`
    """
    matched = match.group(0)
    # We have to escape ';', because that is our
    # escape sequence identifier (otherwise, the escaping)
    # couldn't distinguish between us adding ';_' to the string
    # and ';_' appearing naturally in the string
    if matched == ';':
        return ';;'
    elif matched == '/':
        return ';_'
    else:
        return matched


def quote_slashes(text):
    """
    Quote '/' characters so that they aren't visible to
    django's url quoting, unquoting, or url regex matching.

    Escapes '/'' to the sequence ';_', and ';' to the sequence
    ';;'. By making the escape sequence fixed length, and escaping
    identifier character ';', we are able to reverse the escaping.
    """
    return re.sub(ur'[;/]', _quote_slashes, text)


def _unquote_slashes(match):
    """
    Helper function for `unquote_slashes`
    """
    matched = match.group(0)
    if matched == ';;':
        return ';'
    elif matched == ';_':
        return '/'
    else:
        return matched


def unquote_slashes(text):
    """
    Unquote slashes quoted by `quote_slashes`
    """
    return re.sub(r'(;;|;_)', _unquote_slashes, text)


def handler_url(block, handler_name, suffix='', query='', thirdparty=False):
    """
    This method matches the signature for `xblock.runtime:Runtime.handler_url()`

    See :method:`xblock.runtime:Runtime.handler_url`
    """
    view_name = 'xblock_handler'
    if handler_name:
        # Be sure this is really a handler.
        #
        # We're checking the .__class__ instead of the block itself to avoid
        # auto-proxying from Descriptor -> Module, in case descriptors want
        # to ask for handler URLs without a student context.
        func = getattr(block.__class__, handler_name, None)
        if not func:
            raise ValueError("{!r} is not a function name".format(handler_name))

        # Is the following necessary? ProxyAttribute causes an UndefinedContext error
        # if trying this without the module system.
        #
        #if not getattr(func, "_is_xblock_handler", False):
        #    raise ValueError("{!r} is not a handler name".format(handler_name))

    if thirdparty:
        view_name = 'xblock_handler_noauth'

    url = reverse(view_name, kwargs={
        'course_id': unicode(block.location.course_key),
        'usage_id': quote_slashes(unicode(block.scope_ids.usage_id).encode('utf-8')),
        'handler': handler_name,
        'suffix': suffix,
    })

    # If suffix is an empty string, remove the trailing '/'
    if not suffix:
        url = url.rstrip('/')

    # If there is a query string, append it
    if query:
        url += '?' + query

    # If third-party, return fully-qualified url
    if thirdparty:
        scheme = "https" if settings.HTTPS == "on" else "http"
        url = '{scheme}://{host}{path}'.format(
            scheme=scheme,
            host=settings.SITE_NAME,
            path=url
        )

    return url


def local_resource_url(block, uri):
    """
    local_resource_url for Studio
    """
    return xblock_local_resource_url(block, uri)


class LmsPartitionService(PartitionService):
    """
    Another runtime mixin that provides access to the student partitions defined on the
    course.

    (If and when XBlock directly provides access from one block (e.g. a split_test_module)
    to another (e.g. a course_module), this won't be necessary, but for now it seems like
    the least messy way to hook things through)

    """
    @property
    def course_partitions(self):
        course = modulestore().get_course(self._course_id)
        return course.user_partitions


class UserTagsService(object):
    """
    A runtime class that provides an interface to the user service.  It handles filling in
    the current course id and current user.
    """

    COURSE_SCOPE = user_course_tag_api.COURSE_SCOPE

    def __init__(self, runtime):
        self.runtime = runtime

    def _get_current_user(self):
        """Returns the real, not anonymized, current user."""
        real_user = self.runtime.get_real_user(self.runtime.anonymous_student_id)
        return real_user

    def get_tag(self, scope, key):
        """
        Get a user tag for the current course and the current user for a given key

            scope: the current scope of the runtime
            key: the key for the value we want
        """
        if scope != user_course_tag_api.COURSE_SCOPE:
            raise ValueError("unexpected scope {0}".format(scope))

        return user_course_tag_api.get_course_tag(
            self._get_current_user(),
            self.runtime.course_id, key
        )

    def set_tag(self, scope, key, value):
        """
        Set the user tag for the current course and the current user for a given key

            scope: the current scope of the runtime
            key: the key that to the value to be set
            value: the value to set
        """
        if scope != user_course_tag_api.COURSE_SCOPE:
            raise ValueError("unexpected scope {0}".format(scope))

        return user_course_tag_api.set_course_tag(
            self._get_current_user(),
            self.runtime.course_id, key, value
        )


class LmsModuleSystem(ModuleSystem):  # pylint: disable=abstract-method
    """
    ModuleSystem specialized to the LMS
    """
    def __init__(self, **kwargs):
        request_cache_dict = RequestCache.get_request_cache().data
        services = kwargs.setdefault('services', {})
        services['fs'] = xblock.reference.plugins.FSService()
        services['i18n'] = ModuleI18nService
        services['library_tools'] = LibraryToolsService(modulestore())
        services['partitions'] = LmsPartitionService(
            user=kwargs.get('user'),
            course_id=kwargs.get('course_id'),
            track_function=kwargs.get('track_function', None),
            cache=request_cache_dict
        )
        store = modulestore()
        services['settings'] = SettingsService()
        services['user_tags'] = UserTagsService(self)
        if badges_enabled():
            services['badging'] = BadgingService(course_id=kwargs.get('course_id'), modulestore=store)
        self.request_token = kwargs.pop('request_token', None)
        super(LmsModuleSystem, self).__init__(**kwargs)

    def handler_url(self, *args, **kwargs):
        """
        Implement the XBlock runtime handler_url interface.

        This is mostly just proxying to the module level `handler_url` function
        defined higher up in this file.

        We're doing this indirection because the module level `handler_url`
        logic is also needed by the `DescriptorSystem`. The particular
        `handler_url` that a `DescriptorSystem` needs will be different when
        running an LMS process or a CMS/Studio process. That's accomplished by
        monkey-patching a global. It's a long story, but please know that you
        can't just refactor and fold that logic into here without breaking
        things.

        https://openedx.atlassian.net/wiki/display/PLAT/Convert+from+Storage-centric+runtimes+to+Application-centric+runtimes

        See :method:`xblock.runtime:Runtime.handler_url`
        """
        return handler_url(*args, **kwargs)

    def local_resource_url(self, *args, **kwargs):
        return local_resource_url(*args, **kwargs)

    def wrap_aside(self, block, aside, view, frag, context):
        """
        Creates a div which identifies the aside, points to the original block,
        and writes out the json_init_args into a script tag.

        The default implementation creates a frag to wraps frag w/ a div identifying the xblock. If you have
        javascript, you'll need to override this impl
        """
        extra_data = {
            'block-id': quote_slashes(unicode(block.scope_ids.usage_id)),
            'url-selector': 'asideBaseUrl',
            'runtime-class': 'LmsRuntime',
        }
        if self.request_token:
            extra_data['request-token'] = self.request_token

        return self._wrap_ele(
            aside,
            view,
            frag,
            extra_data,
        )

    def applicable_aside_types(self, block):
        """
        Return all of the asides which might be decorating this `block`.

        Arguments:
            block (:class:`.XBlock`): The block to render retrieve asides for.
        """

        config = XBlockAsidesConfig.current()

        if not config.enabled:
            return []

        if block.scope_ids.block_type in config.disabled_blocks.split():
            return []

        # TODO: aside_type != 'acid_aside' check should be removed once AcidBlock is only installed during tests
        # (see https://openedx.atlassian.net/browse/TE-811)
        return [
            aside_type
            for aside_type in super(LmsModuleSystem, self).applicable_aside_types(block)
            if aside_type != 'acid_aside'
        ]
