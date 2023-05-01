"""
Soical Sharing mixin for XBlocks and XModules
"""

from xblock.core import XBlockMixin
from xblock.fields import Scope, String

# Make '_' a no-op so we can scrape strings. Using lambda instead of
#  `django.utils.translation.gettext_noop` because Django cannot be imported in this file
_ = lambda text: text


class SocialSharingMixin(XBlockMixin):
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
    social_sharing = String(
        display_name=_("Social Sharing"),
        help=_("Allow this video to be sharable to social media"),
        default=None,
        scope=Scope.content,
    )

    @classmethod
    def parse_social_sharing_from_xml(cls, definition, node):
        """
        When importing an XBlock from XML, this method will parse the license
        information out of the XML and attach it to the block.
        It is defined here so that classes that use this mixin can simply refer
        to this method, rather than reimplementing it in their XML import
        functions.
        """
        social_sharing = node.get('social_sharing', default=False)  # pylint: disable=redefined-builtin
        if social_sharing:
            definition['social_sharing'] = social_sharing
        return definition

    def add_social_sharing_to_xml(self, node, default=None):
        """
        When generating XML from an XBlock, this method will add the XBlock's
        license to the XML representation before it is serialized.
        It is defined here so that classes that use this mixin can simply refer
        to this method, rather than reimplementing it in their XML export
        functions.
        """
        if getattr(self, "social_sharing", default):
            node.set('social_sharing', self.social_sharing)