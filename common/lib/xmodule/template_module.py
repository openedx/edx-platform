import json

from x_module import XModule, XModuleDescriptor
from lxml import etree


class ModuleDescriptor(XModuleDescriptor):
    pass


class Module(XModule):
    """
    This module supports tags of the form
    <customtag option="val" option2="val2">
        <impl>$tagname</impl>
    </customtag>

    In this case, $tagname should refer to a file in data/custom_tags, which contains
    a mako template that uses ${option} and ${option2} for the content.

    For instance:

    data/custom_tags/book::
        More information given in <a href="/book/${page}">the text</a>

    course.xml::
        ...
        <customtag page="234"><impl>book</impl></customtag>
        ...

    Renders to::
        More information given in <a href="/book/234">the text</a>
    """
    def get_state(self):
        return json.dumps({})

    @classmethod
    def get_xml_tags(c):
        return ['customtag']

    def get_html(self):
        return self.html

    def __init__(self, system, xml, item_id, state=None):
        XModule.__init__(self, system, xml, item_id, state)
        xmltree = etree.fromstring(xml)
        filename = xmltree.find('impl').text
        params = dict(xmltree.items())
        self.html = self.system.render_template(filename, params, namespace='custom_tags')
