import logging

from lxml import etree
from pkg_resources import resource_string

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from xblock.core import Scope, String

log = logging.getLogger(__name__)


class AnnotatableFields(object):
    data = String(help="XML data for the annotation", scope=Scope.content)


class AnnotatableModule(AnnotatableFields, XModule):
    js = {'coffee': [resource_string(__name__, 'js/src/javascript_loader.coffee'),
                     resource_string(__name__, 'js/src/collapsible.coffee'),
                     resource_string(__name__, 'js/src/html/display.coffee'),
                     resource_string(__name__, 'js/src/annotatable/display.coffee')],
          'js': []}
    js_module_name = "Annotatable"
    css = {'scss': [resource_string(__name__, 'css/annotatable/display.scss')]}
    icon_class = 'annotatable'

    def __init__(self, *args, **kwargs):
        XModule.__init__(self, *args, **kwargs)

        xmltree = etree.fromstring(self.data)

        self.instructions = self._extract_instructions(xmltree)
        self.content = etree.tostring(xmltree, encoding='unicode')
        self.element_id = self.location.html_id()
        self.highlight_colors = ['yellow', 'orange', 'purple', 'blue', 'green']

    def _get_annotation_class_attr(self, index, el):
        """ Returns a dict with the CSS class attribute to set on the annotation
            and an XML key to delete from the element.
         """

        attr = {}
        cls = ['annotatable-span', 'highlight']
        highlight_key = 'highlight'
        color = el.get(highlight_key)

        if color is not None:
            if color in self.highlight_colors:
                cls.append('highlight-' + color)
            attr['_delete'] = highlight_key
        attr['value'] = ' '.join(cls)

        return {'class': attr}

    def _get_annotation_data_attr(self, index, el):
        """ Returns a dict in which the keys are the HTML data attributes
            to set on the annotation element. Each data attribute has a
            corresponding 'value' and (optional) '_delete' key to specify
            an XML attribute to delete.
        """

        data_attrs = {}
        attrs_map = {
            'body': 'data-comment-body',
            'title': 'data-comment-title',
            'problem': 'data-problem-id'
        }

        for xml_key in attrs_map.keys():
            if xml_key in el.attrib:
                value = el.get(xml_key, '')
                html_key = attrs_map[xml_key]
                data_attrs[html_key] = {'value': value, '_delete': xml_key}

        return data_attrs

    def _render_annotation(self, index, el):
        """ Renders an annotation element for HTML output.  """
        attr = {}
        attr.update(self._get_annotation_class_attr(index, el))
        attr.update(self._get_annotation_data_attr(index, el))

        el.tag = 'span'

        for key in attr.keys():
            el.set(key, attr[key]['value'])
            if '_delete' in attr[key] and attr[key]['_delete'] is not None:
                delete_key = attr[key]['_delete']
                del el.attrib[delete_key]

    def _render_content(self):
        """ Renders annotatable content with annotation spans and returns HTML. """
        xmltree = etree.fromstring(self.content)
        xmltree.tag = 'div'
        if 'display_name' in xmltree.attrib:
            del xmltree.attrib['display_name']

        index = 0
        for el in xmltree.findall('.//annotation'):
            self._render_annotation(index, el)
            index += 1

        return etree.tostring(xmltree, encoding='unicode')

    def _extract_instructions(self, xmltree):
        """ Removes <instructions> from the xmltree and returns them as a string, otherwise None. """
        instructions = xmltree.find('instructions')
        if instructions is not None:
            instructions.tag = 'div'
            xmltree.remove(instructions)
            return etree.tostring(instructions, encoding='unicode')
        return None

    def get_html(self):
        """ Renders parameters to template. """
        context = {
            'display_name': self.display_name_with_default,
            'element_id': self.element_id,
            'instructions_html': self.instructions,
            'content_html': self._render_content()
        }

        return self.system.render_template('annotatable.html', context)


class AnnotatableDescriptor(AnnotatableFields, RawDescriptor):
    module_class = AnnotatableModule
    template_dir_name = "annotatable"
    mako_template = "widgets/raw-edit.html"
