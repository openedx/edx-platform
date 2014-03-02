"""
Module for Image annotations using annotator.
"""
import datetime
from lxml import etree
from pkg_resources import resource_string

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from xblock.core import Scope, String
from xmodule.firebase_token_generator import create_token

import textwrap


class AnnotatableFields(object):
    """ Fields for `ImageModule` and `ImageDescriptor`. """
    data = String(help="XML data for the annotation", scope=Scope.content, default=textwrap.dedent("""\
        <annotatable>
            <instructions>
                <p>
                    Add the instructions to the assignment here.
                </p>
            </instructions>
            <json>
                navigatorSizeRatio: 0.25,
                wrapHorizontal:     true,
                tileSources:   [{
                    Image:  {
                        xmlns: "http://schemas.microsoft.com/deepzoom/2009",
                        Url: "http://static.seadragon.com/content/misc/milwaukee_files/",
                        TileSize: "254",
                        Overlap: "1",
                        Format: "jpg",
                        ServerFormat: "Default",
                        showNavigationControl: true,
                        showNavigator: true,
                        Size: {
                            Width: "15497",
                            Height: "5378"
                        }
                    }
                },],
            </json>
        </annotatable>
        """))
    display_name = String(
        display_name="Display Name",
        help="Display name for this module",
        scope=Scope.settings,
        default='Image Annotation',
    )
    annotation_storage_url = String(help="Location of Annotation backend", scope=Scope.settings, default="http://your_annotation_storage.com", display_name="Url for Annotation Storage")


class ImageAnnotationModule(AnnotatableFields, XModule):
    '''Image Annotation Module'''
    js = {'coffee': [resource_string(__name__, 'js/src/javascript_loader.coffee'),
                     resource_string(__name__, 'js/src/collapsible.coffee'),
                     resource_string(__name__, 'js/src/html/display.coffee'),
                     resource_string(__name__, 'js/src/annotatable/display.coffee')
                     ],
          'js': []}
    css = {'scss': [resource_string(__name__, 'css/annotatable/display.scss')]}
    icon_class = 'imageannotation'

    def __init__(self, *args, **kwargs):
        super(ImageAnnotationModule, self).__init__(*args, **kwargs)

        xmltree = etree.fromstring(self.data)

        self.instructions = self._extract_instructions(xmltree)
        self.openseadragonjson = self.remove_html_markup(etree.tostring(xmltree.find('json'), encoding='unicode'))
        self.user = ""
        if self.runtime.get_real_user is not None:
            self.user = self.runtime.get_real_user(self.runtime.anonymous_student_id).email

    def _extract_instructions(self, xmltree):
        """ Removes <instructions> from the xmltree and returns them as a string, otherwise None. """
        instructions = xmltree.find('instructions')
        if instructions is not None:
            instructions.tag = 'div'
            xmltree.remove(instructions)
            return etree.tostring(instructions, encoding='unicode')
        return None

    def remove_html_markup(self, s):
        tag = False
        quote = False
        out = ""

        for c in s:
            if c == '<' and not quote:
                tag = True
            elif c == '>' and not quote:
                tag = False
            elif (c == '"' or c == "'") and tag:
                quote = not quote
            elif not tag:
                out = out + c

        return out

    def token(self, userId):
        '''
        Return a token for the backend of annotations.
        It uses the course id to retrieve a variable that contains the secret
        token found in inheritance.py. It also contains information of when
        the token was issued. This will be stored with the user along with
        the id for identification purposes in the backend.
        '''
        dtnow = datetime.datetime.now()
        dtutcnow = datetime.datetime.utcnow()
        delta = dtnow - dtutcnow
        newhour, newmin = divmod((delta.days * 24 * 60 * 60 + delta.seconds + 30) // 60, 60)
        newtime = "%s%+02d:%02d" % (dtnow.isoformat(), newhour, newmin)
        if "annotation_token_secret" in dir(self):
            secret = self.annotation_token_secret
        else:
            secret = "NoKeyFound"
        custom_data = {"issuedAt": newtime, "consumerKey": secret, "userId": userId, "ttl": 86400}
        newtoken = create_token(secret, custom_data)
        return newtoken

    def get_html(self):
        """ Renders parameters to template. """
        context = {
            'display_name': self.display_name_with_default,
            'instructions_html': self.instructions,
            'annotation_storage': self.annotation_storage_url,
            'openseadragonjson': self.openseadragonjson,
            'token': self.token(self.user)
        }

        return self.system.render_template('imageannotation.html', context)


class ImageAnnotationDescriptor(AnnotatableFields, RawDescriptor):
    ''' Image annotation descriptor '''
    module_class = ImageAnnotationModule
    mako_template = "widgets/raw-edit.html"

    @property
    def non_editable_metadata_fields(self):
        non_editable_fields = super(ImageAnnotationDescriptor, self).non_editable_metadata_fields
        non_editable_fields.extend([
            ImageAnnotationDescriptor.annotation_storage_url
        ])
        return non_editable_fields
