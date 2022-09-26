"""
Module implementing `xblock.runtime.Runtime` functionality for the LMS
"""

from django.conf import settings
from django.urls import reverse

from lms.djangoapps.lms_xblock.models import XBlockAsidesConfig
from openedx.core.djangoapps.user_api.course_tag import api as user_course_tag_api
from openedx.core.lib.url_utils import quote_slashes
from openedx.core.lib.xblock_utils import wrap_xblock_aside, xblock_local_resource_url
from xmodule.x_module import ModuleSystem  # lint-amnesty, pylint: disable=wrong-import-order


def handler_url(block, handler_name, suffix='', query='', thirdparty=False):
    """
    This method matches the signature for `xblock.runtime:Runtime.handler_url()`

    :param block: The block to generate the url for
    :param handler_name: The handler on that block that the url should resolve to
    :param suffix: Any path suffix that should be added to the handler url
    :param query: Any query string that should be added to the handler url
        (which should not include an initial ? or &)
    :param thirdparty: If true, return a fully-qualified URL instead of relative
        URL. This is useful for URLs to be used by third-party services.
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
            raise ValueError(f"{handler_name!r} is not a function name")

    if thirdparty:
        view_name = 'xblock_handler_noauth'

    url = reverse(view_name, kwargs={
        'course_id': str(block.scope_ids.usage_id.context_key),
        'usage_id': quote_slashes(str(block.scope_ids.usage_id)),
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


class UserTagsService:
    """
    A runtime class that provides an interface to the user service.  It handles filling in
    the current course id and current user.
    """

    COURSE_SCOPE = user_course_tag_api.COURSE_SCOPE

    def __init__(self, user, course_id):
        self._user = user
        self._course_id = course_id

    def get_tag(self, scope, key):
        """
        Get a user tag for the current course and the current user for a given key

            scope: the current scope of the runtime
            key: the key for the value we want
        """
        if scope != user_course_tag_api.COURSE_SCOPE:
            raise ValueError(f"unexpected scope {scope}")

        return user_course_tag_api.get_course_tag(
            self._user,
            self._course_id, key
        )

    def set_tag(self, scope, key, value):
        """
        Set the user tag for the current course and the current user for a given key

            scope: the current scope of the runtime
            key: the key that to the value to be set
            value: the value to set
        """
        if scope != user_course_tag_api.COURSE_SCOPE:
            raise ValueError(f"unexpected scope {scope}")

        return user_course_tag_api.set_course_tag(
            self._user,
            self._course_id, key, value
        )


class LmsModuleSystem(ModuleSystem):  # pylint: disable=abstract-method
    """
    ModuleSystem specialized to the LMS
    """
    def __init__(self, **kwargs):
        self.request_token = kwargs.pop('request_token', None)
        super().__init__(**kwargs)

    def handler_url(self, *args, **kwargs):  # lint-amnesty, pylint: disable=signature-differs
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
        if not frag.content:
            return frag

        runtime_class = 'LmsRuntime'
        extra_data = {
            'block-id': quote_slashes(str(block.scope_ids.usage_id)),
            'course-id': quote_slashes(str(block.course_id)),
            'url-selector': 'asideBaseUrl',
            'runtime-class': runtime_class,
        }
        if self.request_token:
            extra_data['request-token'] = self.request_token

        return wrap_xblock_aside(
            runtime_class,
            aside,
            view,
            frag,
            context,
            usage_id_serializer=str,
            request_token=self.request_token,
            extra_data=extra_data,
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
            for aside_type in super().applicable_aside_types(block)
            if aside_type != 'acid_aside'
        ]
