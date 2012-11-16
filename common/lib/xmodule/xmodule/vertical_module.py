from .xmodule import XModule, register_view
from .progress import Progress
from .module_resources import render_template

# HACK: This shouldn't be hard-coded to two types
# OBSOLETE: This obsoletes 'type'
class_priority = ['video', 'problem']


class VerticalModule(XModule):
    ''' Layout module for laying out submodules vertically.'''

    @register_view('student_view')
    def get_html(self):
        return render_template('vert_module.html', {
            'items': [self.render_child(child) for child in self.children]
        })

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
