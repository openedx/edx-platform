"""
Mixin to support editing in Studio.
"""
from xmodule.x_module import module_attr, STUDENT_VIEW, AUTHOR_VIEW


class StudioEditableBlock(object):
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
            fragment.add_frag_resources(rendered_child)

            contents.append({
                'id': unicode(child.location),
                'content': rendered_child.content
            })

        fragment.add_content(self.system.render_template("studio_render_children_view.html", {  # pylint: disable=no-member
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


class StudioEditableDescriptor(object):
    """
    Helper mixin for supporting Studio editing of xmodules.

    This class is only intended to be used with an XModule Descriptor. This class assumes that the associated
    XModule will have an "author_view" method for returning an editable preview view of the module.
    """
    author_view = module_attr(AUTHOR_VIEW)
    has_author_view = True


def has_author_view(descriptor):
    """
    Returns True if the xmodule linked to the descriptor supports "author_view".
    """
    return getattr(descriptor, 'has_author_view', False)
