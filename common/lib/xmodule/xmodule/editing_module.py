"""Descriptors for XBlocks/Xmodules, that provide editing of atrributes"""

from pkg_resources import resource_string
from xmodule.mako_module import MakoModuleDescriptor
from xblock.fields import Scope, String
import logging

log = logging.getLogger(__name__)


class EditingFields(object):
    """Contains specific template information (the raw data body)"""
    data = String(scope=Scope.content, default='')


class EditingDescriptor(EditingFields, MakoModuleDescriptor):
    """
    Module that provides a raw editing view of its data and children.  It does not
    perform any validation on its definition---just passes it along to the browser.

    This class is intended to be used as a mixin.
    """
    resources_dir = None

    mako_template = "widgets/raw-edit.html"

    @property
    def non_editable_metadata_fields(self):
        """
        `data` should not be editable in the Studio settings editor.
        """
        non_editable_fields = super(EditingDescriptor, self).non_editable_metadata_fields
        non_editable_fields.append(self.fields['data'])
        return non_editable_fields

    # cdodge: a little refactoring here, since we're basically doing the same thing
    # here as with our parent class, let's call into it to get the basic fields
    # set and then add our additional fields. Trying to keep it DRY.
    def get_context(self):
        _context = MakoModuleDescriptor.get_context(self)
        # Add our specific template information (the raw data body)
        _context.update({'data': self.data})
        return _context


class TabsEditingDescriptor(EditingFields, MakoModuleDescriptor):
    """
    Module that provides a raw editing view of its data and children.  It does not
    perform any validation on its definition---just passes it along to the browser.

    This class is intended to be used as a mixin.

    Engine (module_edit.js) wants for metadata editor
    template to be always loaded, so don't forget to include
    settings tab in your module descriptor.
    """
    mako_template = "widgets/tabs-aggregator.html"
    css = {'scss': [resource_string(__name__, 'css/tabs/tabs.scss')]}
    js = {'coffee': [resource_string(
        __name__, 'js/src/tabs/tabs-aggregator.coffee')]}
    js_module_name = "TabsEditingDescriptor"
    tabs = []

    def get_context(self):
        _context = super(TabsEditingDescriptor, self).get_context()
        _context.update({
            'tabs': self.tabs,
            'html_id': self.location.html_id(),  # element_id
            'data': self.data,
        })
        return _context

    @classmethod
    def get_css(cls):
        # load every tab's css
        for tab in cls.tabs:
            tab_styles = tab.get('css', {})
            for css_type, css_content in tab_styles.items():
                if css_type in cls.css:
                    cls.css[css_type].extend(css_content)
                else:
                    cls.css[css_type] = css_content
        return cls.css


class XMLEditingDescriptor(EditingDescriptor):
    """
    Module that provides a raw editing view of its data as XML. It does not perform
    any validation of its definition
    """

    css = {'scss': [resource_string(__name__, 'css/codemirror/codemirror.scss')]}

    js = {'coffee': [resource_string(__name__, 'js/src/raw/edit/xml.coffee')]}
    js_module_name = "XMLEditingDescriptor"


class MetadataOnlyEditingDescriptor(EditingDescriptor):
    """
    Module which only provides an editing interface for the metadata, it does
    not expose a UI for editing the module data
    """

    js = {'coffee': [resource_string(__name__, 'js/src/raw/edit/metadata-only.coffee')]}
    js_module_name = "MetadataOnlyEditingDescriptor"

    mako_template = "widgets/metadata-only-edit.html"


class JSONEditingDescriptor(EditingDescriptor):
    """
    Module that provides a raw editing view of its data as XML. It does not perform
    any validation of its definition
    """

    css = {'scss': [resource_string(__name__, 'css/codemirror/codemirror.scss')]}

    js = {'coffee': [resource_string(__name__, 'js/src/raw/edit/json.coffee')]}
    js_module_name = "JSONEditingDescriptor"
