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
        Renders the children of the module with HTML appropriate for Studio. If can_reorder is True,
        then the children will be rendered to support drag and drop.
        """
        contents = []

        for child in self.get_children():  # pylint: disable=no-member
            if can_reorder:
                context['reorderable_items'].add(child.location)
            context['can_add'] = can_add
            rendered_child = child.render(StudioEditableModule.get_preview_view_name(child), context)
            fragment.add_fragment_resources(rendered_child)

            contents.append({
                'id': str(child.location),
                'content': rendered_child.content
            })

        fragment.add_content(self.runtime.service(self, 'mako').render_template("studio_render_children_view.html", {  # pylint: disable=no-member
            'items': contents,
            'xblock_context': context,
            'can_add': can_add,
            'can_reorder': can_reorder,
        }))

    @staticmethod
    def get_preview_view_name(block):
        """
        Helper method for getting preview view name (student_view or author_view) for a given module.
        """
        return AUTHOR_VIEW if has_author_view(block) else STUDENT_VIEW


StudioEditableModule = StudioEditableBlock


def has_author_view(descriptor):
    """
    Returns True if the xmodule linked to the descriptor supports "author_view".
    """
    return getattr(descriptor, 'has_author_view', False)
