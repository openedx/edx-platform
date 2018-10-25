from __future__ import absolute_import, print_function, unicode_literals
import warnings

from edxmako.shortcuts import render_to_string


class RuntimeShim(object):
    """
    All the old/deprecated APIs that our XBlock runtime(s) need to
    support are captured in this mixin.
    """
    @property
    def error_tracker(self):
        warnings.warn(
            "Use of system.error_tracker is deprecated; use self.runtime.service(self, 'error_tracker') instead",
            DeprecationWarning, stacklevel=2,
        )
        return None  # We can't access the service here since we don't know what block is asking.

    def get_policy(self, _usage_id):
        """
        A function that takes a usage id and returns a dict of policy to apply.
        """
        # TODO: implement?
        return {}

    def render_template(self, template_name, dictionary, namespace='main'):
        """
        Render a mako template
        """
        warnings.warn(
            "Use of runtime.render_template is deprecated. "
            "Use xblockutils.resources.ResourceLoader.render_mako_template or a JavaScript-based template instead.",
            DeprecationWarning, stacklevel=2,
        )
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


class XBlockShim(object):
    """
    Mixin added to XBlock classes in this runtime, to support
    older/XModule APIs
    """
    @property
    def location(self):
        warnings.warn(
            "Use of block.location should be replaced with block.scope_ids.usage_id",
            DeprecationWarning, stacklevel=2,
        )
        return self.scope_ids.usage_id

    @property
    def system(self):
        warnings.warn(
            "Use of block.system should be replaced with block.runtime",
            DeprecationWarning, stacklevel=2,
        )
        return self.runtime
