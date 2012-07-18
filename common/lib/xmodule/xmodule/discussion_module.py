from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor


class DiscussionModule(XModule):
    def get_html(self):
        return "Discussion: To be implemented"

    def __init__(self, system, location, definition, instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, instance_state, shared_state, **kwargs)
        print "Initialized"
        print definition

class DiscussionDescriptor(RawDescriptor):
    module_class = DiscussionModule
