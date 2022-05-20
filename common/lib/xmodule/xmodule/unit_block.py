"""
An XBlock which groups related XBlocks together.

This is like the "vertical" block, but without that block's UI code, JavaScript,
and other legacy features.
"""


from web_fragments.fragment import Fragment
from xblock.completable import XBlockCompletionMode
from xblock.core import XBlock
from xblock.fields import Scope, String

# Make '_' a no-op so we can scrape strings.
_ = lambda text: text


class UnitBlock(XBlock):
    """
    Unit XBlock: An XBlock which groups related XBlocks together.

    This is like the "vertical" block in principle, but this version is
    explicitly designed to not contain LMS-related logic, like vertical does.

    The application which renders XBlocks and/or the runtime should manage
    things like bookmarks, completion tracking, etc.
    This version also avoids any XModule mixins and has no JavaScript code.
    """
    has_children = True
    # This is a block containing other blocks, so its completion is defined by
    # the completion of its child blocks:
    completion_mode = XBlockCompletionMode.AGGREGATOR
    # Define a non-existent resources dir because we don't have resources, but
    # the default will pull in all files in this folder.
    resources_dir = 'assets/unit'

    display_name = String(
        display_name=_("Display Name"),
        help=_("The display name for this component."),
        scope=Scope.settings,
        default=_("Unit"),
    )

    def student_view(self, context=None):
        """Provide default student view."""
        result = Fragment()

        # TODO: uncomment this line and remove _render_children() once
        # merger of ModuleSystem and DescriptorSystem is complete

        # child_frags = self.runtime.render_children(self, context=context)
        child_frags = self._render_children(context)

        result.add_resources(child_frags)
        result.add_content('<div class="unit-xblock vertical">')
        for frag in child_frags:
            result.add_content(frag.content)
        result.add_content('</div>')
        return result

    def _render_children(self, context):
        """
        Use CombinedSystem runtime to get block and render each child individually.

        The runtime.render_children() method was earlier used to render each child
        However, this caused a problem, when we removed the get_block() and
        descriptor_runtime properties from the ModuleSystem, as the render_children
        method ran in the context of LmsModuleSystem which is a child class of
        ModuleSystem.

        This is intended to be a temporary method until deprecation of all properties
        of ModuleSystem and merger of ModuleSystem and DescriptorSystem is complete.
        """
        results = []
        for child_id in self.children:
            child = self.runtime.get_block(child_id)
            result = self.runtime.render_child(child, context=context)
            results.append(result)
        return results

    public_view = student_view

    def index_dictionary(self):
        """
        Return dictionary prepared with module content and type for indexing, so
        that the contents of this block can be found in free-text searches.
        """
        # return key/value fields in a Python dict object
        # values may be numeric / string or dict
        xblock_body = super().index_dictionary()
        index_body = {
            "display_name": self.display_name,
        }
        if "content" in xblock_body:
            xblock_body["content"].update(index_body)
        else:
            xblock_body["content"] = index_body
        # We use "Sequence" for sequentials and units/verticals
        xblock_body["content_type"] = "Sequence"

        return xblock_body
