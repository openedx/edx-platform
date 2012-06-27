from xmodule.x_module import XModule
from xmodule.seq_module import SequenceDescriptor
from xmodule.progress import Progress


class VerticalModule(XModule):
    ''' Layout module for laying out submodules vertically.'''
    def get_html(self):
        return self.system.render_template('vert_module.html', {
            'items': self.contents
        })

    def get_progress(self):
        # TODO: Cache progress or children array?
        children = self.get_children()
        progresses = [child.get_progress() for child in children]
        progress = reduce(Progress.add_counts, progresses)
        return progress

    def __init__(self, system, location, definition, instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, instance_state, shared_state, **kwargs)
        self.contents = [child.get_html() for child in self.get_display_items()]


class VerticalDescriptor(SequenceDescriptor):
    module_class = VerticalModule
