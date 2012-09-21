from pkg_resources import resource_string
from lxml import etree
from xmodule.mako_module import MakoModuleDescriptor
import logging

log = logging.getLogger(__name__)

class EditingDescriptor(MakoModuleDescriptor):
    """
    Module that provides a raw editing view of its data and children.  It does not
    perform any validation on its definition---just passes it along to the browser.

    This class is intended to be used as a mixin.
    """
    mako_template = "widgets/raw-edit.html"

    js = {'coffee': [resource_string(__name__, 'js/src/raw/edit.coffee')]}
    js_module_name = "RawDescriptor"

    def get_context(self):
        return {
            'module': self,
            'data': self.definition.get('data', ''),
            'metadata': self.metadata
    # TODO (vshnayder): allow children and metadata to be edited.
    #'children' : self.definition.get('children, ''),

    # TODO: show both own metadata and inherited?
    #'metadata' : self.own_metadata,
        }
