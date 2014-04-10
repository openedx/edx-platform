from xblock.fragment import Fragment
from xmodule.x_module import XModule
from xmodule.seq_module import SequenceDescriptor
from xmodule.progress import Progress
from pkg_resources import resource_string

# HACK: This shouldn't be hard-coded to two types
# OBSOLETE: This obsoletes 'type'
class_priority = ['video', 'problem']


class VerticalFields(object):
    has_children = True


class VerticalModule(VerticalFields, XModule):
    ''' Layout module for laying out submodules vertically.'''

    def student_view(self, context):
        fragment = Fragment()
        contents = []

        for child in self.get_display_items():
            rendered_child = child.render('student_view', context)
            fragment.add_frag_resources(rendered_child)

            contents.append({
                'id': child.location.to_deprecated_string(),
                'content': rendered_child.content
            })

        fragment.add_content(self.system.render_template('vert_module.html', {
            'items': contents
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
