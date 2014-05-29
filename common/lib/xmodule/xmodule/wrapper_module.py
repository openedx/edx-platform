# Same as vertical,
# But w/o css delimiters between children

from xmodule.vertical_module import VerticalModule, VerticalDescriptor
from pkg_resources import resource_string

# HACK: This shouldn't be hard-coded to two types
# OBSOLETE: This obsoletes 'type'
class_priority = ['video', 'problem']


class WrapperModule(VerticalModule):
    ''' Layout module for laying out submodules vertically w/o css delimiters'''

    has_children = True
    css = {'scss': [resource_string(__name__, 'css/wrapper/display.scss')]}


class WrapperDescriptor(VerticalDescriptor):
    module_class = WrapperModule

    has_children = True
