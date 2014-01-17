import logging

from lxml import etree
from pkg_resources import resource_string

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from xblock.core import Scope, String

import textwrap

log = logging.getLogger(__name__)


class AnnotatableFields(object):
    """ Fields for `VideoModule` and `VideoDescriptor`. """
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
    sourceurl = String(help="The external source URL for the video.", display_name="Source URL", scope=Scope.settings, default="http://video-js.zencoder.com/oceans-clip.mp4")
    poster_url = String(help="Poster Image URL", display_name="Poster URL", scope=Scope.settings, default="")
    annotation_storage_url = String(help="Location of Annotation backend", scope=Scope.settings, default="http://your_annotation_storage.com", display_name="Url for Annotation Storage")


class VideoAnnotationModule(AnnotatableFields, XModule):
    '''Video Annotation Module'''
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

    def _get_annotation_class_attr(self, element):
        """ Returns a dict with the CSS class attribute to set on the annotation
            and an XML key to delete from the element.
         """

        attr = {}
        cls = ['annotatable-span', 'highlight']
        highlight_key = 'highlight'
        color = element.get(highlight_key)

        if color is not None:
            if color in self.highlight_colors:
                cls.append('highlight-' + color)
            attr['_delete'] = highlight_key
        attr['value'] = ' '.join(cls)

        return {'class': attr}

    def _get_annotation_data_attr(self, element):
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
            if xml_key in element.attrib:
                value = element.get(xml_key, '')
                html_key = attrs_map[xml_key]
                data_attrs[html_key] = {'value': value, '_delete': xml_key}

        return data_attrs

    def _render_annotation(self, index, element):
        """ Renders an annotation element for HTML output.  """
        attr = {}
        attr.update(self._get_annotation_class_attr(index, element))
        attr.update(self._get_annotation_data_attr(index, element))

        element.tag = 'span'

        for key in attr.keys():
            element.set(key, attr[key]['value'])
            if '_delete' in attr[key] and attr[key]['_delete'] is not None:
                delete_key = attr[key]['_delete']
                del element.attrib[delete_key]

    def _render_content(self):
        """ Renders annotatable content with annotation spans and returns HTML. """
        xmltree = etree.fromstring(self.content)
        xmltree.tag = 'div'
        if 'display_name' in xmltree.attrib:
            del xmltree.attrib['display_name']

        index = 0
        for element in xmltree.findall('.//annotation'):
            self._render_annotation(index, element)
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

    def _get_extension(self, srcurl):
        ''' get the extension of a given url '''
        if 'youtu' in srcurl:
            return 'video/youtube'
        else:
            spliturl = srcurl.split(".")
            extensionplus1 = spliturl[len(spliturl) - 1]
            spliturl = extensionplus1.split("?")
            extensionplus2 = spliturl[0]
            spliturl = extensionplus2.split("#")
            return 'video/' + spliturl[0]

    def get_html(self):
        """ Renders parameters to template. """
        extension = self._get_extension(self.sourceurl)

        context = {
            'display_name': self.display_name_with_default,
            'element_id': self.element_id,
            'instructions_html': self.instructions,
            'sourceUrl': self.sourceurl,
            'typeSource': extension,
            'poster': self.poster_url,
            'alert': self,
            'content_html': self._render_content(),
            'annotation_storage': self.annotation_storage_url
        }

        return self.system.render_template('videoannotation.html', context)


class VideoAnnotationDescriptor(AnnotatableFields, RawDescriptor):
    ''' Video annotation descriptor '''
    module_class = VideoAnnotationModule
    mako_template = "widgets/raw-edit.html"
