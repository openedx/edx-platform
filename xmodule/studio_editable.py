"""
Mixin to support editing in Studio.
"""
from xblock.core import XBlock, XBlockMixin

from xmodule.x_module import AUTHOR_VIEW, STUDENT_VIEW


@XBlock.needs('mako')
class StudioEditableBlock(XBlockMixin):
    """
    Helper methods for supporting Studio editing of XBlocks.

    This class is only intended to be used with an XBlock!
    """

    has_author_view = True

    def render_children(self, context, fragment, can_reorder=False, can_add=False):
        """
        Renders the children of the block with HTML appropriate for Studio. If can_reorder is True,
        then the children will be rendered to support drag and drop.
        """
        contents = []

        for child in self.get_children():  # pylint: disable=no-member
            if can_reorder:
                context['reorderable_items'].add(child.location)
            context['can_add'] = can_add
            rendered_child = child.render(StudioEditableBlock.get_preview_view_name(child), context)
            fragment.add_fragment_resources(rendered_child)

            contents.append({
                'id': str(child.location),
                'content': rendered_child.content
            })

        mako_service = self.runtime.service(self, 'mako')
        # For historic reasons, this template is in the LMS folder, and some code like xblock-utils expects that.
        fragment.add_content(mako_service.render_lms_template("studio_render_children_view.html", {  # pylint: disable=no-member
            'items': contents,
            'xblock_context': context,
            'can_add': can_add,
            'can_reorder': can_reorder,
        }))

    @staticmethod
    def get_preview_view_name(block):
        """
        Helper method for getting preview view name (student_view or author_view) for a given block.
        """
        return AUTHOR_VIEW if has_author_view(block) else STUDENT_VIEW


def has_author_view(block):
    """
    Returns True if the xmodule linked to the block supports "author_view".
    """
    return getattr(block, 'has_author_view', False)
