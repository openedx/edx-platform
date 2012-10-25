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

    def get_html(self):
        return self.descriptor.rendered_html


class CustomTagDescriptor(RawDescriptor):
    """ Descriptor for custom tags.  Loads the template when created."""
    module_class = CustomTagModule
    template_dir_name = 'customtag'

    @staticmethod
    def render_template(system, xml_data):
        '''Render the template, given the definition xml_data'''
        xmltree = etree.fromstring(xml_data)
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
            return Template(template.read()).render(**params)


    def __init__(self, system, definition, **kwargs):
        '''Render and save the template for this descriptor instance'''
        super(CustomTagDescriptor, self).__init__(system, definition, **kwargs)
        self.rendered_html = self.render_template(system, definition['data'])

    def export_to_file(self):
        """
        Custom tags are special: since they're already pointers, we don't want
        to export them in a file with yet another layer of indirection.
        """
        return False

