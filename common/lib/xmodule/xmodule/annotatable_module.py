import logging

from lxml import etree
from pkg_resources import resource_string

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from xblock.fields import Scope, String
import textwrap

log = logging.getLogger(__name__)

# Make '_' a no-op so we can scrape strings. Using lambda instead of
#  `django.utils.translation.ugettext_noop` because Django cannot be imported in this file
_ = lambda text: text


class AnnotatableFields(object):
    data = String(
        help=_("XML data for the annotation"),
        scope=Scope.content,
        default=textwrap.dedent("""
        <annotatable>
            <instructions>
                <p>Enter your (optional) instructions for the exercise in HTML format.</p>
                <p>Annotations are specified by an <code>&lt;annotation&gt;</code> tag which may may have the following attributes:</p>
                <ul class="instructions-template">
                    <li><code>title</code> (optional). Title of the annotation. Defaults to <i>Commentary</i> if omitted.</li>
                    <li><code>body</code> (<b>required</b>). Text of the annotation.</li>
                    <li><code>problem</code> (optional). Numeric index of the problem associated with this annotation. This is a zero-based index, so the first problem on the page would have <code>problem="0"</code>.</li>
                    <li><code>highlight</code> (optional). Possible values: yellow, red, orange, green, blue, or purple. Defaults to yellow if this attribute is omitted.</li>
                </ul>
            </instructions>
            <p>Add your HTML with annotation spans here.</p>
            <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. <annotation title="My title" body="My comment" highlight="yellow" problem="0">Ut sodales laoreet est, egestas gravida felis egestas nec.</annotation> Aenean at volutpat erat. Cras commodo viverra nibh in aliquam.</p>
            <p>Nulla facilisi. <annotation body="Basic annotation example." problem="1">Pellentesque id vestibulum libero.</annotation> Suspendisse potenti. Morbi scelerisque nisi vitae felis dictum mattis. Nam sit amet magna elit. Nullam volutpat cursus est, sit amet sagittis odio vulputate et. Curabitur euismod, orci in vulputate imperdiet, augue lorem tempor purus, id aliquet augue turpis a est. Aenean a sagittis libero. Praesent fringilla pretium magna, non condimentum risus elementum nec. Pellentesque faucibus elementum pharetra. Pellentesque vitae metus eros.</p>
        </annotatable>
        """)
    )
    display_name = String(
        display_name=_("Display Name"),
        help=_("The display name for this component."),
        scope=Scope.settings,
        default=_('Annotation'),
    )


class AnnotatableModule(AnnotatableFields, XModule):
    js = {
        'coffee': [
            resource_string(__name__, 'js/src/html/display.coffee'),
            resource_string(__name__, 'js/src/annotatable/display.coffee'),
        ],
        'js': [
            resource_string(__name__, 'js/src/javascript_loader.js'),
            resource_string(__name__, 'js/src/collapsible.js'),
        ]
    }
    js_module_name = "Annotatable"
    css = {'scss': [resource_string(__name__, 'css/annotatable/display.scss')]}
    icon_class = 'annotatable'

    def __init__(self, *args, **kwargs):
        super(AnnotatableModule, self).__init__(*args, **kwargs)

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
            'display_name': self.display_name_with_default_escaped,
            'element_id': self.element_id,
            'instructions_html': self.instructions,
            'content_html': self._render_content()
        }

        return self.system.render_template('annotatable.html', context)


class AnnotatableDescriptor(AnnotatableFields, RawDescriptor):
    module_class = AnnotatableModule
    mako_template = "widgets/raw-edit.html"
    resources_dir = None
