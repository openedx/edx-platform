"""
Module for Image annotations using annotator.
"""
from lxml import etree
from pkg_resources import resource_string

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from xblock.core import Scope, String
from xmodule.annotator_mixin import get_instructions, html_to_text
from xmodule.annotator_token import retrieve_token
from xblock.fragment import Fragment

import textwrap

# Make '_' a no-op so we can scrape strings
_ = lambda text: text


class AnnotatableFields(object):
    """ Fields for `ImageModule` and `ImageDescriptor`. """
    data = String(
        help=_("XML data for the annotation"),
        scope=Scope.content,
        default=textwrap.dedent("""\
        <annotatable>
            <instructions>
                <p>
                    Add the instructions to the assignment here.
                </p>
            </instructions>
            <p>
                Lorem ipsum dolor sit amet, at amet animal petentium nec. Id augue nemore postulant mea. Ex eam dicant noluisse expetenda, alia admodum abhorreant qui et. An ceteros expetenda mea, tale natum ipsum quo no, ut pro paulo alienum noluisse.
            </p>
            <json>
                navigatorSizeRatio: 0.25,
                wrapHorizontal:     false,
                showNavigator: true,
                navigatorPosition: "BOTTOM_LEFT",
                showNavigationControl: true,
                tileSources:    [{"profile": "http://library.stanford.edu/iiif/image-api/1.1/compliance.html#level2", "scale_factors": [1, 2, 4, 8, 16, 32, 64], "tile_height": 1024, "height": 3466, "width": 113793, "tile_width": 1024, "qualities": ["native", "bitonal", "grey", "color"], "formats": ["jpg", "png", "gif"], "@context": "http://library.stanford.edu/iiif/image-api/1.1/context.json", "@id": "http://54.187.32.48/loris/suzhou_orig.jp2"}],
            </json>
        </annotatable>
        """))
    display_name = String(
        display_name=_("Display Name"),
        help=_("Display name for this module"),
        scope=Scope.settings,
        default=_('Image Annotation'),
    )
    instructor_tags = String(
        display_name=_("Tags for Assignments"),
        help=_("Add tags that automatically highlight in a certain color using the comma-separated form, i.e. imagery:red,parallelism:blue"),
        scope=Scope.settings,
        default='professor:green,teachingAssistant:blue',
    )
    annotation_storage_url = String(
        help=_("Location of Annotation backend"),
        scope=Scope.settings,
        default="http://your_annotation_storage.com",
        display_name=_("Url for Annotation Storage")
    )
    annotation_token_secret = String(
        help=_("Secret string for annotation storage"),
        scope=Scope.settings,
        default="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        display_name=_("Secret Token String for Annotation")
    )
    default_tab = String(
        display_name=_("Default Annotations Tab"),
        help=_("Select which tab will be the default in the annotations table: myNotes, Instructor, or Public."),
        scope=Scope.settings,
        default="myNotes",
    )
    # currently only supports one instructor, will build functionality for multiple later
    instructor_email = String(
        display_name=_("Email for 'Instructor' Annotations"),
        help=_("Email of the user that will be attached to all annotations that will be found in 'Instructor' tab."),
        scope=Scope.settings,
        default="",
    )
    annotation_mode = String(
        display_name=_("Mode for Annotation Tool"),
        help=_("Type in number corresponding to following modes:  'instructor' or 'everyone'"),
        scope=Scope.settings,
        default="everyone",
    )


class ImageAnnotationModule(AnnotatableFields, XModule):
    '''Image Annotation Module'''
    js = {
        'coffee': [
            resource_string(__name__, 'js/src/javascript_loader.coffee'),
            resource_string(__name__, 'js/src/html/display.coffee'),
            resource_string(__name__, 'js/src/annotatable/display.coffee'),
        ],
        'js': [
            resource_string(__name__, 'js/src/collapsible.js'),
        ]
    }
    css = {'scss': [resource_string(__name__, 'css/annotatable/display.scss')]}
    icon_class = 'imageannotation'

    def __init__(self, *args, **kwargs):
        super(ImageAnnotationModule, self).__init__(*args, **kwargs)

        xmltree = etree.fromstring(self.data)

        self.instructions = self._extract_instructions(xmltree)
        self.openseadragonjson = html_to_text(etree.tostring(xmltree.find('json'), encoding='unicode'))
        self.user_email = ""
        self.is_course_staff = False
        if self.runtime.get_user_role() in ['instructor', 'staff']:
            self.is_course_staff = True
        if self.runtime.get_real_user is not None:
            try:
                self.user_email = self.runtime.get_real_user(self.runtime.anonymous_student_id).email
            except Exception:  # pylint: disable=broad-except
                self.user_email = _("No email address found.")

    def _extract_instructions(self, xmltree):
        """ Removes <instructions> from the xmltree and returns them as a string, otherwise None. """
        return get_instructions(xmltree)

    def student_view(self, context):
        """ Renders parameters to template. """
        context = {
            'display_name': self.display_name_with_default,
            'instructions_html': self.instructions,
            'token': retrieve_token(self.user_email, self.annotation_token_secret),
            'tag': self.instructor_tags,
            'openseadragonjson': self.openseadragonjson,
            'annotation_storage': self.annotation_storage_url,
            'default_tab': self.default_tab,
            'instructor_email': self.instructor_email,
            'annotation_mode': self.annotation_mode,
            'is_course_staff': self.is_course_staff,
        }
        fragment = Fragment(self.system.render_template('imageannotation.html', context))

        # TinyMCE already exists in Studio so we should not load the files again
        # get_real_user always returns "None" in Studio since its runtimes contains no anonymous ids
        if self.runtime.get_real_user is not None:
            fragment.add_javascript_url(self.runtime.STATIC_URL + "js/vendor/tinymce/js/tinymce/tinymce.full.min.js")
            fragment.add_javascript_url(self.runtime.STATIC_URL + "js/vendor/tinymce/js/tinymce/jquery.tinymce.min.js")
        return fragment


class ImageAnnotationDescriptor(AnnotatableFields, RawDescriptor):  # pylint: disable=abstract-method
    ''' Image annotation descriptor '''
    module_class = ImageAnnotationModule
    mako_template = "widgets/raw-edit.html"

    @property
    def non_editable_metadata_fields(self):
        non_editable_fields = super(ImageAnnotationDescriptor, self).non_editable_metadata_fields
        non_editable_fields.extend([
            ImageAnnotationDescriptor.annotation_storage_url,
            ImageAnnotationDescriptor.annotation_token_secret,
        ])
        return non_editable_fields
