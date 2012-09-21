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

    def get_context(self):
        return {
            'module': self,
            'data': self.definition.get('data', ''),
    # TODO (vshnayder): allow children and metadata to be edited.
    #'children' : self.definition.get('children, ''),

    # TODO: show both own metadata and inherited?
    #'metadata' : self.own_metadata,
        }


class XMLEditingDescriptor(EditingDescriptor):
    """
    Module that provides a raw editing view of its data as XML. It does not perform
    any validation of its definition
    """

    js = {'coffee': [resource_string(__name__, 'js/src/raw/edit/xml.coffee')]}
    js_module_name = "XMLEditingDescriptor"


class JSONEditingDescriptor(EditingDescriptor):
    """
    Module that provides a raw editing view of its data as XML. It does not perform
    any validation of its definition
    """

    js = {'coffee': [resource_string(__name__, 'js/src/raw/edit/json.coffee')]}
    js_module_name = "JSONEditingDescriptor"
