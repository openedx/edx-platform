from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor


class HiddenModule(XModule):
    pass


class HiddenDescriptor(RawDescriptor):
    module_class = HiddenModule
