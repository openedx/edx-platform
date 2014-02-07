"""
Module for Video annotations using annotator.
"""
from lxml import etree
from pkg_resources import resource_string

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from xblock.core import Scope, String

import textwrap


class AnnotatableFields(object):
    """ Fields for `VideoModule` and `VideoDescriptor`. """
    data = String(help="XML data for the annotation", scope=Scope.content, default=textwrap.dedent("""\
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
                     resource_string(__name__, 'js/src/annotatable/display.coffee')
                     ],
          'js': []}
    css = {'scss': [resource_string(__name__, 'css/annotatable/display.scss')]}
    icon_class = 'videoannotation'

    def __init__(self, *args, **kwargs):
        super(VideoAnnotationModule, self).__init__(*args, **kwargs)

        xmltree = etree.fromstring(self.data)

        self.instructions = self._extract_instructions(xmltree)
        self.content = etree.tostring(xmltree, encoding='unicode')

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
            'instructions_html': self.instructions,
            'sourceUrl': self.sourceurl,
            'typeSource': extension,
            'poster': self.poster_url,
            'annotation_storage': self.annotation_storage_url
        }

        return self.system.render_template('videoannotation.html', context)


class VideoAnnotationDescriptor(AnnotatableFields, RawDescriptor):
    ''' Video annotation descriptor '''
    module_class = VideoAnnotationModule
    mako_template = "widgets/raw-edit.html"

    @property
    def non_editable_metadata_fields(self):
        non_editable_fields = super(VideoAnnotationDescriptor, self).non_editable_metadata_fields
        non_editable_fields.extend([
            VideoAnnotationDescriptor.annotation_storage_url
        ])
        return non_editable_fields
