"""
Template block
"""

from string import Template
from xblock.core import XBlock

from lxml import etree
from pkg_resources import resource_string
from web_fragments.fragment import Fragment
from xmodule.editing_block import EditingMixin
from xmodule.raw_block import RawMixin
from xmodule.util.xmodule_django import add_webpack_to_fragment
from xmodule.x_module import (
    HTMLSnippet,
    ResourceTemplates,
    shim_xmodule_js,
    XModuleMixin,
    XModuleToXBlockMixin,
)
from xmodule.xml_block import XmlMixin

from openedx.core.djangolib.markup import Text


class CustomTagTemplateBlock(  # pylint: disable=abstract-method
    RawMixin,
    XmlMixin,
    EditingMixin,
    XModuleToXBlockMixin,
    HTMLSnippet,
    ResourceTemplates,
    XModuleMixin,
):
    """
    A block which provides templates for CustomTagBlock. The template name
    is set on the `impl` attribute of CustomTagBlock. See below for more details
    on how to use it.
    """


@XBlock.needs('mako')
class CustomTagBlock(CustomTagTemplateBlock):  # pylint: disable=abstract-method
    """
    This block supports tags of the form
    <customtag option="val" option2="val2" impl="tagname"/>

    In this case, $tagname should refer to a file in data/custom_tags, which
    contains a Python string.Template formatted template that uses ${option} and
    ${option2} for the content.

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
    resources_dir = None
    template_dir_name = 'customtag'

    preview_view_js = {
        'js': [],
        'xmodule_js': resource_string(__name__, 'js/src/xmodule.js'),
    }
    preview_view_css = {
        'scss': [],
    }
    studio_view_js = {
        'js': [resource_string(__name__, 'js/src/raw/edit/xml.js')],
        'xmodule_js': resource_string(__name__, 'js/src/xmodule.js'),
    }
    studio_view_css = {
        'scss': [resource_string(__name__, 'css/codemirror/codemirror.scss')],
    }

    def studio_view(self, _context):
        """
        Return the studio view.
        """
        fragment = Fragment(
            self.runtime.service(self, 'mako').render_template(self.mako_template, self.get_context())
        )
        add_webpack_to_fragment(fragment, 'CustomTagBlockStudio')
        shim_xmodule_js(fragment, 'XMLEditingDescriptor')
        return fragment

    def render_template(self, system, xml_data):
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
                raise Exception("Could not find impl attribute in customtag {}"
                                .format(self.location))

        params = dict(list(xmltree.items()))

        # cdodge: look up the template as a module
        template_loc = self.location.replace(category='custom_tag_template', name=template_name)

        template_block = system.get_block(template_loc)
        template_block_data = template_block.data
        template = Template(template_block_data)
        return template.safe_substitute(params)

    @property
    def rendered_html(self):
        return self.render_template(self.runtime, self.data)

    def student_view(self, _context):
        """
        Renders the student view.
        """
        fragment = Fragment()
        fragment.add_content(self.rendered_html)
        return fragment

    def export_to_file(self):
        """
        Custom tags are special: since they're already pointers, we don't want
        to export them in a file with yet another layer of indirection.
        """
        return False


class TranslateCustomTagBlock(  # pylint: disable=abstract-method
    XModuleToXBlockMixin,
    XModuleMixin,
):
    """
    Converts olx of the form `<$custom_tag attr="" attr=""/>` to CustomTagBlock
    of the form `<customtag attr="" attr="" impl="$custom_tag"/>`.
    """
    resources_dir = None

    @classmethod
    def parse_xml(cls, node, runtime, _keys, _id_generator):
        """
        Transforms the xml_data from <$custom_tag attr="" attr=""/> to
        <customtag attr="" attr="" impl="$custom_tag"/>
        """

        runtime.error_tracker(Text('WARNING: the <{tag}> tag is deprecated.  '
                              'Instead, use <customtag impl="{tag}" attr1="..." attr2="..."/>. ')
                              .format(tag=node.tag))

        tag = node.tag
        node.tag = 'customtag'
        node.attrib['impl'] = tag

        return runtime.process_xml(etree.tostring(node))
