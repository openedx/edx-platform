"""
Code to implement backwards compatibility
"""
# pylint: disable=no-member

import hashlib
import warnings

from django.conf import settings
from django.core.cache import cache
from django.template import TemplateDoesNotExist
from django.utils.functional import cached_property
from fs.memoryfs import MemoryFS
from openedx.core.djangoapps.xblock.apps import get_xblock_app_config
import six

from common.djangoapps.edxmako.shortcuts import render_to_string


class RuntimeShim(object):
    """
    All the old/deprecated APIs that our XBlock runtime(s) need to
    support are captured in this mixin.
    """

    def __init__(self, *args, **kwargs):
        super(RuntimeShim, self).__init__(*args, **kwargs)
        self._active_block = None

    def render(self, block, view_name, context=None):
        """
        Render a block by invoking its view.
        """
        # The XBlock runtime code assumes a runtime is long-lived and serves
        # multiple blocks. But the previous edX runtime had a separate runtime
        # instance for each XBlock instance. So in order to implement its API,
        # we need this hacky way to get the "current" XBlock. As XBlocks are
        # modified to not use these deprecated APIs, this should be used less
        # and less
        old_active_block = self._active_block
        self._active_block = block
        try:
            return super(RuntimeShim, self).render(block, view_name, context)
        finally:
            # Reset the active view to what it was before entering this method
            self._active_block = old_active_block

    def handle(self, block, handler_name, request, suffix=''):
        """
        Render a block by invoking its view.
        """
        # See comment in render() above
        old_active_block = self._active_block
        self._active_block = block
        try:
            return super(RuntimeShim, self).handle(block, handler_name, request, suffix)
        finally:
            # Reset the active view to what it was before entering this method
            self._active_block = old_active_block

    @property
    def anonymous_student_id(self):
        """
        Get an anonymized identifier for this user.
        """
        # To do? Change this to a runtime service or method so that we can have
        # access to the context_key without relying on self._active_block.
        if self.user.is_anonymous:
            # This is an anonymous user, and the self.user_id value is already
            # an anonymous string. It's not anonymized per course, but we don't
            # really care since this user's XBlock data is ephemeral and is only
            # kept around for a day or two anyways.
            return self.user_id
        #### TEMPORARY IMPLEMENTATION:
        # TODO: Update student.models.AnonymousUserId to have a 'context_key'
        # column instead of 'course_key' (no DB migration needed). Then change
        # this to point to the existing student.models.anonymous_id_for_user
        # code. (Or do we want a separate new table for the new runtime?)
        # The reason we can't do this now is that ContextKey doesn't yet exist
        # in the opaque-keys repo, so there is no working 'ContextKeyField'
        # class in opaque-keys that accepts either old CourseKeys or new
        # LearningContextKeys.
        hasher = hashlib.md5()
        hasher.update(settings.SECRET_KEY.encode('utf-8'))
        hasher.update(six.text_type(self.user_id).encode('utf-8'))
        digest = hasher.hexdigest()
        return digest

    @property
    def cache(self):
        """
        Access to a cache.

        Seems only to be used by capa. Remove this if capa can be refactored.
        """
        # TODO: Refactor capa to access this directly, don't bother the runtime. Then remove it from here.
        return cache

    @property
    def can_execute_unsafe_code(self):
        """
        Determine if capa problems in this context/course are allowed to run
        unsafe code. See common/lib/xmodule/xmodule/util/sandboxing.py

        Seems only to be used by capa.
        """
        # TODO: Refactor capa to access this directly, don't bother the runtime. Then remove it from here.
        return False  # Change this if/when we need to support unsafe courses in the new runtime.

    @property
    def DEBUG(self):
        """
        Should DEBUG mode (?) be used? This flag is only read by capa.
        """
        # TODO: Refactor capa to access this directly, don't bother the runtime. Then remove it from here.
        return False

    def get_python_lib_zip(self):
        """
        A function returning a bytestring or None. The bytestring is the
        contents of a zip file that should be importable by other Python code
        running in the module.

        Only used for capa problems.
        """
        # TODO: load the python code from Blockstore. Ensure it's not publicly accessible.
        return None

    @property
    def error_tracker(self):
        """
        Accessor for the course's error tracker
        """
        warnings.warn(
            "Use of system.error_tracker is deprecated; use self.runtime.service(self, 'error_tracker') instead",
            DeprecationWarning, stacklevel=2,
        )
        return self.service(self._active_block, 'error_tracker')

    def get_policy(self, _usage_id):
        """
        A function that takes a usage id and returns a dict of policy to apply.
        """
        # TODO: implement?
        return {}

    @property
    def filestore(self):
        """
        Alternate name for 'resources_fs'. Not sure if either name is deprecated
        but we should deprecate one :)
        """
        return self.resources_fs

    @property
    def node_path(self):
        """
        Get the path to Node.js

        Seems only to be used by capa. Remove this if capa can be refactored.
        """
        # TODO: Refactor capa to access this directly, don't bother the runtime. Then remove it from here.
        return getattr(settings, 'NODE_PATH', None)  # Only defined in the LMS

    def render_template(self, template_name, dictionary, namespace='main'):
        """
        Render a mako template
        """
        warnings.warn(
            "Use of runtime.render_template is deprecated. "
            "Use xblockutils.resources.ResourceLoader.render_mako_template or a JavaScript-based template instead.",
            DeprecationWarning, stacklevel=2,
        )
        try:
            return render_to_string(template_name, dictionary, namespace=namespace)
        except TemplateDoesNotExist:
            # From Studio, some templates might be in the LMS namespace only
            return render_to_string(template_name, dictionary, namespace="lms." + namespace)

    def process_xml(self, xml):
        """
        Code to handle parsing of child XML for old blocks that use XmlParserMixin.
        """
        # We can't parse XML in a vacuum - we need to know the parent block and/or the
        # OLX file that holds this XML in order to generate useful definition keys etc.
        # The older ImportSystem runtime could do this because it stored the course_id
        # as part of the runtime.
        raise NotImplementedError("This newer runtime does not support process_xml()")

    def replace_urls(self, html_str):
        """
        Deprecated precursor to transform_static_paths_to_urls

        Given an HTML string, replace any static file paths like
            /static/foo.png
        (which are really pointing to block-specific assets stored in blockstore)
        with working absolute URLs like
            https://s3.example.com/blockstore/bundle17/this-block/assets/324.png
        See common/djangoapps/static_replace/__init__.py

        This is generally done automatically for the HTML rendered by XBlocks,
        but if an XBlock wants to have correct URLs in data returned by its
        handlers, the XBlock must call this API directly.

        Note that the paths are only replaced if they are in "quotes" such as if
        they are an HTML attribute or JSON data value. Thus, to transform only a
        single path string on its own, you must pass html_str=f'"{path}"'
        """
        return self.transform_static_paths_to_urls(self._active_block, html_str)

    def replace_course_urls(self, html_str):
        """
        Given an HTML string, replace any course-relative URLs like
            /course/blah
        with working URLs like
            /course/:course_id/blah
        See common/djangoapps/static_replace/__init__.py
        """
        # TODO: implement or deprecate.
        # See also the version in openedx/core/lib/xblock_utils/__init__.py
        return html_str

    def replace_jump_to_id_urls(self, html_str):
        """
        Replace /jump_to_id/ URLs in the HTML with expanded versions.
        See common/djangoapps/static_replace/__init__.py
        """
        # TODO: implement or deprecate.
        # See also the version in openedx/core/lib/xblock_utils/__init__.py
        return html_str

    @property
    def resources_fs(self):
        """
        A filesystem that XBlocks can use to read large binary assets.
        """
        # TODO: implement this to serve any static assets that
        # self._active_block has in its blockstore "folder". But this API should
        # be deprecated and we should instead get compatible XBlocks to use a
        # runtime filesystem service. Some initial exploration of that (as well
        # as of the 'FileField' concept) has been done and is included in the
        # XBlock repo at xblock.reference.plugins.FSService and is available in
        # the old runtime as the 'fs' service.
        warnings.warn(
            "Use of legacy runtime.resources_fs or .filestore won't be able to find resources.",
            stacklevel=3,
        )
        fake_fs = MemoryFS()
        fake_fs.root_path = 'mem://'  # Required for the video XBlock's use of edxval create_transcript_objects
        return fake_fs

    export_fs = object()  # Same as above, see resources_fs ^

    @property
    def seed(self):
        """
        A number to seed the random number generator. Used by capa and the
        randomize module.

        Should be based on the user ID, per the existing implementation.
        """
        # TODO: Refactor capa to use the user ID or anonymous ID as the seed, don't bother the runtime.
        # Then remove it from here.
        return self.user_id if self.user_id is not None else 0

    @property
    def STATIC_URL(self):
        """
        Get the django STATIC_URL path.

        Seems only to be used by capa. Remove this if capa can be refactored.
        """
        # TODO: Refactor capa to access this directly, don't bother the runtime. Then remove it from here.
        static_url = settings.STATIC_URL
        if static_url.startswith('/') and not static_url.startswith('//'):
            # This is not a full URL - should start with https:// to support loading assets from an iframe sandbox
            site_root_url = get_xblock_app_config().get_site_root_url()
            static_url = site_root_url + static_url
        return static_url

    @cached_property
    def user_is_staff(self):
        """
        Is the current user a global staff user?
        """
        warnings.warn(
            "runtime.user_is_staff is deprecated. Use the user service instead:\n"
            "    user = self.runtime.service(self, 'user').get_current_user()\n"
            "    is_staff = user.opt_attrs.get('edx-platform.user_is_staff')",
            DeprecationWarning, stacklevel=2,
        )
        if self.user and self.user.is_authenticated:
            return self.user.is_staff
        return False

    @cached_property
    def xqueue(self):
        """
        An accessor for XQueue, the platform's interface for external grader
        services.

        Seems only to be used by capa. Remove this if capa can be refactored.
        """
        # TODO: Refactor capa to access this directly, don't bother the runtime. Then remove it from here.
        return {
            'interface': None,
            'construct_callback': None,
            'default_queuename': None,
            'waittime': 5,  # seconds; should come from settings.XQUEUE_WAITTIME_BETWEEN_REQUESTS
        }

    def get_field_provenance(self, xblock, field):
        """
        A Studio-specific method that was implemented on DescriptorSystem.
        Used by the problem block.

        For the given xblock, return a dict for the field's current state:
        {
            'default_value': what json'd value will take effect if field is unset: either the field default or
            inherited value,
            'explicitly_set': boolean for whether the current value is set v default/inherited,
        }
        """
        result = {}
        result['explicitly_set'] = xblock._field_data.has(xblock, field.name)  # pylint: disable=protected-access
        try:
            result['default_value'] = xblock._field_data.default(xblock, field.name)  # pylint: disable=protected-access
        except KeyError:
            result['default_value'] = field.to_json(field.default)
        return result

    def track_function(self, title, event_info):
        """
        Publish an event to the tracking log.

        This is deprecated in favor of runtime.publish
        See https://git.io/JeGLf and https://git.io/JeGLY for context.
        """
        warnings.warn(
            "runtime.track_function is deprecated. Use runtime.publish() instead.",
            DeprecationWarning, stacklevel=2,
        )
        self.publish(self._active_block, title, event_info)

    @property
    def user_location(self):
        """
        Old API to get the user's country code (or None)
        Used by the Video XBlock to select a CDN for user.
        """
        # Studio always returned None so we just return None for now.
        # TBD: support this API or deprecate+remove it.
        return None

    @property
    def course_id(self):
        """
        Old API to get the course ID.
        """
        warnings.warn(
            "runtime.course_id is deprecated. Use context_key instead:\n"
            "    block.scope_ids.usage_id.context_key\n",
            DeprecationWarning, stacklevel=2,
        )
        return self._active_block.scope_ids.usage_id.context_key

    def _css_classes_for(self, block, view):
        """
        Get the list of CSS classes that the wrapping <div> should have for the
        specified xblock or aside's view.
        """
        css_classes = super(RuntimeShim, self)._css_classes_for(block, view)
        # Many CSS styles for former XModules use
        # .xmodule_display.xmodule_VideoBlock
        # as their selector, so add those classes:
        if view in ('student_view', 'public_view'):
            css_classes.append('xmodule_display')
        elif view == 'studio_view':
            css_classes.append('xmodule_edit')
        css_classes.append('xmodule_{}'.format(block.unmixed_class.__name__))
        return css_classes


class XBlockShim(object):
    """
    Mixin added to XBlock classes in this runtime, to support
    older/XModule APIs
    """
    @property
    def location(self):
        """
        Accessor for the usage ID
        """
        warnings.warn(
            "Use of block.location should be replaced with block.scope_ids.usage_id",
            DeprecationWarning, stacklevel=2,
        )
        return self.scope_ids.usage_id

    @property
    def system(self):
        """
        Accessor for the XModule runtime
        """
        warnings.warn(
            "Use of block.system should be replaced with block.runtime",
            DeprecationWarning, stacklevel=2,
        )
        return self.runtime

    @property
    def graded(self):
        """
        Not sure what this is or how it's supposed to be set. Capa seems to
        expect a 'graded' attribute to be present on itself. Possibly through
        contentstore's update_section_grader_type() ?
        """
        if self.scope_ids.block_type != 'problem':
            raise AttributeError(".graded shim is only for capa")
        return False

    # Attributes defined by XModuleMixin and sometimes used by the LMS
    # Set sensible defaults.
    # If any of these are meant to be used in new stuff (are not deprecated)
    # they should be moved to xblock.runtime.mixin.LmsBlockMixin and documented
    always_recalculate_grades = False
    show_in_read_only_mode = False
    icon_class = 'other'

    def get_icon_class(self):
        """
        Return a css class identifying this module in the context of an icon
        """
        return self.icon_class

    def has_dynamic_children(self):
        """
        Returns True if this XBlock has dynamic children for a given
        student when the module is created. This is deprecated and discouraged.
        """
        return False

    def get_display_items(self):
        """
        Returns a list of descendent XBlock instances that will display
        immediately inside this module.
        """
        warnings.warn("get_display_items() is deprecated.", DeprecationWarning, stacklevel=2)
        items = []
        for child in self.get_children():
            items.extend(child.displayable_items())
        return items

    def displayable_items(self):
        """
        Returns list of displayable modules contained by this XBlock. If this
        module is visible, should return [self].
        """
        return [self]
