from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from lxml import etree


class CustomTagModule(XModule):
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

    def __init__(self, system, location, definition, instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, instance_state, shared_state, **kwargs)
        xmltree = etree.fromstring(self.definition['data'])
        filename = xmltree.find('impl').text
        params = dict(xmltree.items())
        self.html = self.system.render_template(filename, params, namespace='custom_tags')

    def get_html(self):
        return self.html


class CustomTagDescriptor(RawDescriptor):
    module_class = CustomTagModule
