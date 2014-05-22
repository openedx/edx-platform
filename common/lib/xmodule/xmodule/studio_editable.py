"""
Mixin to support editing in Studio.
"""


class StudioEditableModule(object):
    """
    Helper methods for supporting Studio editing of xblocks.
    """

    def render_reorderable_children(self, context, fragment):
        """
        Renders children with the appropriate HTML structure for drag and drop.
        """
        contents = []

        for child in self.get_display_items():
            context['reorderable_items'].add(child.location)
            rendered_child = child.render('student_view', context)
            fragment.add_frag_resources(rendered_child)

            contents.append({
                'id': child.id,
                'content': rendered_child.content
            })

        fragment.add_content(self.system.render_template("studio_render_children_view.html", {
            'items': contents,
            'xblock_context': context,
        }))
