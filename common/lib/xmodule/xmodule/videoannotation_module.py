import logging

from lxml import etree
from pkg_resources import resource_string

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from xblock.core import Scope, String

import textwrap
from mimetypes import guess_type, guess_extension

log = logging.getLogger(__name__)

class AnnotatableFields(object):
    """Fields for `VideoModule` and `VideoDescriptor`."""
    data = String(help="XML data for the annotation", scope=Scope.content,
        default=textwrap.dedent(
        """\
        <annotatable>
            <instructions>
                <p>
                	Add the instructions to the assignment here. 
                </p>
            </instructions>
        </annotatable>
        """))
    display_name = String(
        display_name="Display Name",
        help="Display name for this module",
        scope=Scope.settings,
        default='Video Annotation',
    )
    sourceUrl = String(help="The external source URL for the video.", display_name="Source URL", scope=Scope.settings, default="http://video-js.zencoder.com/oceans-clip.mp4")
    poster_url = String(help="Poster Image URL", display_name="Poster URL", scope=Scope.settings, default="")

class VideoAnnotationModule(AnnotatableFields, XModule):
    js = {'coffee': [resource_string(__name__, 'js/src/javascript_loader.coffee'),
                     resource_string(__name__, 'js/src/collapsible.coffee'),
                     resource_string(__name__, 'js/src/html/display.coffee'),
                     resource_string(__name__, 'js/src/annotatable/display.coffee')],
          'js': []
    }
#    js_module_name = "VideoAnnotation"
    css = {'scss': [resource_string(__name__, 'css/annotatable/display.scss')]}
    icon_class = 'videoannotation'

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
    
    def _get_extension(self,srcURL):
        if 'youtu' in srcURL:
            return 'video/youtube'
        else:
            spliturl = srcURL.split(".")
            extensionPlus1 = spliturl[len(spliturl)-1]
            spliturl = extensionPlus1.split("?")
            extensionPlus2 = spliturl[0]
            spliturl = extensionPlus2.split("#")
            return 'video/' + spliturl[0]
    
    def get_html(self):
        """ Renders parameters to template. """
        extension = self._get_extension(self.sourceUrl)

        context = {
            'display_name': self.display_name_with_default,
            'element_id': self.element_id,
            'instructions_html': self.instructions,
            'sourceUrl': self.sourceUrl,
            'typeSource': extension,
            'poster': self.poster_url,
            'alert': self,
            'content_html': self._render_content(),
            'annotation_storage':self.annotation_storage_url
        }

        return self.system.render_template('videoannotation.html', context)


class VideoAnnotationDescriptor(AnnotatableFields, RawDescriptor):
    module_class = VideoAnnotationModule
    mako_template = "widgets/raw-edit.html"
