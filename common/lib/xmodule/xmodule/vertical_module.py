from xmodule.x_module import XModule
from xmodule.seq_module import SequenceDescriptor
from xmodule.progress import Progress
from pkg_resources import resource_string

# HACK: This shouldn't be hard-coded to two types
# OBSOLETE: This obsoletes 'type'
class_priority = ['video', 'problem']


class VerticalModule(XModule):
    ''' Layout module for laying out submodules vertically.'''

    js = {'coffee': [resource_string(__name__,
                                     'js/src/vertical/display.coffee')]}
    css = {'scss': [resource_string(__name__, 'css/vertical/display.scss')]}
    js_module_name = "Vertical"

    def __init__(self, system, location, definition, descriptor, instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, descriptor, instance_state, shared_state, **kwargs)
        self.contents = None

    def get_html(self):
        if self.contents is None:
            self.contents = [child.get_html() for child in self.get_display_items()]

        return self.system.render_template('vert_module.html', {
            'items': self.contents
        })

    def get_progress(self):
        """
        Combine the progress of all the children.
        """
        # TODO: check if children are mixed as to video or problem, so
        # that add_counts does the right thing.  
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


class VerticalDescriptor(SequenceDescriptor):
    module_class = VerticalModule
