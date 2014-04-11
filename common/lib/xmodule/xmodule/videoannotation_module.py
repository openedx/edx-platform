"""
Module for Video annotations using annotator.
"""
from lxml import etree
from pkg_resources import resource_string

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from xblock.core import Scope, String
from xmodule.annotator_token import retrieve_token
from xmodule.annotator_mixin import get_instructions, get_extension, ANNOTATOR_COMMON_JS, ANNOTATOR_COMMON_CSS

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
    annotation_token_secret = String(help="Secret string for annotation storage", scope=Scope.settings, default="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", display_name="Secret Token String for Annotation")

class VideoAnnotationModule(AnnotatableFields, XModule):
    '''Video Annotation Module'''
    js = {'coffee': [resource_string(__name__, 'js/src/javascript_loader.coffee'),
                     resource_string(__name__, 'js/src/html/display.coffee'),
                     resource_string(__name__, 'js/src/annotatable/display.coffee')
                     ],
          'js': ANNOTATOR_COMMON_JS + [resource_string(__name__, 'js/src/collapsible.js')]}
    css = {'scss': ANNOTATOR_COMMON_CSS + [resource_string(__name__, 'css/annotatable/display.scss')]}
    icon_class = 'videoannotation'

    def __init__(self, *args, **kwargs):
        super(VideoAnnotationModule, self).__init__(*args, **kwargs)

        xmltree = etree.fromstring(self.data)

        self.instructions = self._extract_instructions(xmltree)
        self.content = etree.tostring(xmltree, encoding='unicode')
        self.user = ""
        if self.runtime.get_real_user is not None:
            self.user = self.runtime.get_real_user(self.runtime.anonymous_student_id).email

    def _extract_instructions(self, xmltree):
        """ Removes <instructions> from the xmltree and returns them as a string, otherwise None. """
        return get_instructions(xmltree)

    def _get_extension(self, srcurl):
        ''' get the extension of a given url '''
        return get_extension(srcurl)

    def get_html(self):
        """ Renders parameters to template. """
        extension = self._get_extension(self.sourceurl)

        context = {
            'display_name': self.display_name_with_default,
            'instructions_html': self.instructions,
            'sourceUrl': self.sourceurl,
            'typeSource': extension,
            'poster': self.poster_url,
            'annotation_storage': self.annotation_storage_url,
            'token': retrieve_token(self.user, self.annotation_token_secret),
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
            VideoAnnotationDescriptor.annotation_storage_url,
            VideoAnnotationDescriptor.annotation_token_secret
        ])
        return non_editable_fields
