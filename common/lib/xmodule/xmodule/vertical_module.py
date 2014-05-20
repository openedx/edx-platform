from xblock.fragment import Fragment
from xmodule.x_module import XModule
from xmodule.seq_module import SequenceDescriptor
from xmodule.progress import Progress
from xmodule.studio_editable import StudioEditableModule
from pkg_resources import resource_string
from copy import copy

# HACK: This shouldn't be hard-coded to two types
# OBSOLETE: This obsoletes 'type'
class_priority = ['video', 'problem']


class VerticalFields(object):
    has_children = True


class VerticalModule(VerticalFields, XModule, StudioEditableModule):
    ''' Layout module for laying out submodules vertically.'''

    def student_view(self, context):
        # When rendering a Studio preview, use a different template to support drag and drop.
        if context and context.get('runtime_type', None) == 'studio':
            return self.studio_preview_view(context)

        return self.render_view(context, 'vert_module.html')

    def studio_preview_view(self, context):
        """
        Renders the Studio preview view, which supports drag and drop.
        """
        fragment = Fragment()
        # For the container page we want the full drag-and-drop, but for unit pages we want
        # a more concise version that appears alongside the "View =>" link.
        if context.get('container_view'):
            self.render_children(context, fragment, can_reorder=True, can_add=True)
        return fragment

    def render_view(self, context, template_name):
        """
        Helper method for rendering student_view and the Studio version.
        """
        fragment = Fragment()
        contents = []

        child_context = {} if not context else copy(context)
        child_context['child_of_vertical'] = True

        for child in self.get_display_items():
            rendered_child = child.render('student_view', child_context)
            fragment.add_frag_resources(rendered_child)

            contents.append({
                'id': child.location.to_deprecated_string(),
                'content': rendered_child.content
            })

        fragment.add_content(self.system.render_template(template_name, {
            'items': contents,
            'xblock_context': context,
        }))
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
        for c in class_priority:
            if c in child_classes:
                new_class = c
        return new_class


class VerticalDescriptor(VerticalFields, SequenceDescriptor):
    module_class = VerticalModule

    js = {'coffee': [resource_string(__name__, 'js/src/vertical/edit.coffee')]}
    js_module_name = "VerticalDescriptor"

    # TODO (victor): Does this need its own definition_to_xml method?  Otherwise it looks
    # like verticals will get exported as sequentials...

    @property
    def non_editable_metadata_fields(self):
        non_editable_fields = super(VerticalDescriptor, self).non_editable_metadata_fields
        non_editable_fields.extend([
            VerticalDescriptor.due,
        ])
        return non_editable_fields
