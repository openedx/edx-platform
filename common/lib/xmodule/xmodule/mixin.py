"""
Reusable mixins for XBlocks and/or XModules
"""

from xblock.fields import Scope, String, XBlockMixin

# Make '_' a no-op so we can scrape strings
_ = lambda text: text


class LicenseMixin(XBlockMixin):
    """
    Mixin that allows an author to indicate a license on the contents of an
    XBlock. For example, a video could be marked as Creative Commons SA-BY
    licensed. You can even indicate the license on an entire course.

    If this mixin is not applied to an XBlock, or if the license field is
    blank, then the content is subject to whatever legal licensing terms that
    apply to content by default. For example, in the United States, that content
    is exclusively owned by the creator of the content by default. Other
    countries may have similar laws.
    """
    license = String(
        display_name=_("License"),
        help=_("A license defines how the contents of this block can be shared and reused."),
        default=None,
        scope=Scope.content,
    )

    @classmethod
    def parse_license_from_xml(cls, definition, node):
        """
        When importing an XBlock from XML, this method will parse the license
        information out of the XML and attach it to the block.
        It is defined here so that classes that use this mixin can simply refer
        to this method, rather than reimplementing it in their XML import
        functions.
        """
        license = node.get('license', default=None)  # pylint: disable=redefined-builtin
        if license:
            definition['license'] = license
        return definition

    def add_license_to_xml(self, node, default=None):
        """
        When generating XML from an XBlock, this method will add the XBlock's
        license to the XML representation before it is serialized.
        It is defined here so that classes that use this mixin can simply refer
        to this method, rather than reimplementing it in their XML export
        functions.
        """
        if getattr(self, "license", default):
            node.set('license', self.license)


def wrap_with_license(block, view, frag, context):  # pylint: disable=unused-argument
    """
    In the LMS, display the custom license underneath the XBlock.
    """
    license = getattr(block, "license", None)  # pylint: disable=redefined-builtin
    if license:
        context = {"license": license}
        frag.content += block.runtime.render_template('license_wrapper.html', context)
    return frag
