from pkg_resources import resource_string
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

    # cdodge: a little refactoring here, since we're basically doing the same thing
    # here as with our parent class, let's call into it to get the basic fields
    # set and then add our additional fields. Trying to keep it DRY.
    def get_context(self):
        _context = MakoModuleDescriptor.get_context(self)
        # Add our specific template information (the raw data body)
        _context.update({'data': self.definition.get('data', '')})
        return _context


class XMLEditingDescriptor(EditingDescriptor):
    """
    Module that provides a raw editing view of its data as XML. It does not perform
    any validation of its definition
    """

    css = {'scss': [resource_string(__name__, 'css/codemirror/codemirror.scss')]}

    js = {'coffee': [resource_string(__name__, 'js/src/raw/edit/xml.coffee')]}
    js_module_name = "XMLEditingDescriptor"


class JSONEditingDescriptor(EditingDescriptor):
    """
    Module that provides a raw editing view of its data as XML. It does not perform
    any validation of its definition
    """

    css = {'scss': [resource_string(__name__, 'css/codemirror/codemirror.scss')]}

    js = {'coffee': [resource_string(__name__, 'js/src/raw/edit/json.coffee')]}
    js_module_name = "JSONEditingDescriptor"
