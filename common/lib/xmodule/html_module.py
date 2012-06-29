import json
import logging

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from lxml import etree
from pkg_resources import resource_string

log = logging.getLogger("mitx.courseware")


class HtmlModule(XModule):
    def get_html(self):
        return self.html

    def __init__(self, system, location, definition, instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, instance_state, shared_state, **kwargs)
        self.html = self.definition['data']['text']


class HtmlDescriptor(RawDescriptor):
    """
    Module for putting raw html in a course
    """
    mako_template = "widgets/html-edit.html"
    module_class = HtmlModule

    js = {'coffee': [resource_string(__name__, 'js/module/html.coffee')]}
    js_module = 'HTML'
