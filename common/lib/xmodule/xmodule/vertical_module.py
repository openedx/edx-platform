"""
VerticalBlock - a pure XBlock.
"""
from xblock.core import XBlock
from xblock.fragment import Fragment
from xmodule.x_module import STUDENT_VIEW
from xmodule.seq_module import SequenceDescriptor
from xmodule.progress import Progress
from xmodule.studio_editable import StudioEditableBlock
from pkg_resources import resource_string
from copy import copy


# HACK: This shouldn't be hard-coded to two types
# OBSOLETE: This obsoletes 'type'
CLASS_PRIORITY = ['video', 'problem']


class VerticalBlock(StudioEditableBlock, XBlock):
    ''' Layout module for laying out submodules vertically.'''

    has_children = True

    def student_view(self, context):
        fragment = Fragment()
        contents = []

        child_context = {} if not context else copy(context)
        child_context['child_of_vertical'] = True

        for child in self.get_display_items():
            rendered_child = child.render(STUDENT_VIEW, child_context)
            fragment.add_frag_resources(rendered_child)

            contents.append({
                'id': child.location.to_deprecated_string(),
                'content': rendered_child.content
            })

        fragment.add_content(self.system.render_template('vert_module.html', {
            'items': contents,
            'xblock_context': context,
        }))
        return fragment

    def author_view(self, context):
        """
        Renders the Studio preview view, which supports drag and drop.
        """
        fragment = Fragment()
        root_xblock = context.get('root_xblock')
        is_root = root_xblock and root_xblock.location == self.location

        # For the container page we want the full drag-and-drop, but for unit pages we want
        # a more concise version that appears alongside the "View =>" link-- unless it is
        # the unit page and the vertical being rendered is itself the unit vertical (is_root == True).
        if is_root or not context.get('is_unit_page'):
            self.render_children(context, fragment, can_reorder=True, can_add=True)
        return fragment

    def get_progress(self):
        # TODO: Cache progress or children array?
        children = self.get_children()
        progresses = [child.get_progress() for child in children]
        progress = reduce(Progress.add_counts, progresses, None)
        return progress

    def get_icon_class(self):
        child_classes = set(child.get_icon_class() for child in self.get_children())
        new_class = 'other'
        for higher_class in CLASS_PRIORITY:
            if higher_class in child_classes:
                new_class = higher_class
        return new_class

    @property
    def non_editable_metadata_fields(self):
        """
        Gather all fields which can't be edited.
        """
        non_editable_fields = super(VerticalBlock, self).non_editable_metadata_fields
        non_editable_fields.extend([
            VerticalBlock.due,
        ])
        return non_editable_fields
