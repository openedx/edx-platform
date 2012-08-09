from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from lxml import etree
from mako.template import Template


class CustomTagModule(XModule):
    """
    This module supports tags of the form
    <customtag option="val" option2="val2" impl="tagname"/>

    In this case, $tagname should refer to a file in data/custom_tags, which contains
    a mako template that uses ${option} and ${option2} for the content.

    For instance:

    data/mycourse/custom_tags/book::
        More information given in <a href="/book/${page}">the text</a>

    course.xml::
        ...
        <customtag page="234" impl="book"/>
        ...

    Renders to::
        More information given in <a href="/book/234">the text</a>
    """

    def __init__(self, system, location, definition, descriptor,
                 instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, descriptor,
                         instance_state, shared_state, **kwargs)
        self.html = definition['html']

    def get_html(self):
        return self.html


class CustomTagDescriptor(RawDescriptor):
    """ Descriptor for custom tags.  Loads the template when created."""
    module_class = CustomTagModule

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        definition = RawDescriptor.definition_from_xml(xml_object, system)

        # Render the template and save it.
        xmltree = etree.fromstring(definition['data'])
        if 'impl' in xmltree.attrib:
            template_name = xmltree.attrib['impl']
        else:
            # VS[compat]  backwards compatibility with old nested customtag structure
            child_impl = xmltree.find('impl')
            if child_impl is not None:
                template_name = child_impl.text
            else:
                # TODO (vshnayder): better exception type
                raise Exception("Could not find impl attribute in customtag {0}"
                                .format(location))

        params = dict(xmltree.items())
        with system.resources_fs.open('custom_tags/{name}'
                                   .format(name=template_name)) as template:
            definition['html'] = Template(template.read()).render(**params)

        return definition
