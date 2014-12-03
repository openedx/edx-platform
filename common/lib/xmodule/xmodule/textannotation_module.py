''' Text annotation module '''

from lxml import etree
from pkg_resources import resource_string

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from xblock.core import Scope, String
from xmodule.annotator_mixin import get_instructions
from xmodule.annotator_token import retrieve_token
from xblock.fragment import Fragment
import textwrap

# Make '_' a no-op so we can scrape strings
_ = lambda text: text


class AnnotatableFields(object):
    """Fields for `TextModule` and `TextDescriptor`."""
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
        </annotatable>
        """))
    display_name = String(
        display_name=_("Display Name"),
        help=_("Display name for this module"),
        scope=Scope.settings,
        default=_('Text Annotation'),
    )
    instructor_tags = String(
        display_name=_("Tags for Assignments"),
        help=_("Add tags that automatically highlight in a certain color using the comma-separated form, i.e. imagery:red,parallelism:blue"),
        scope=Scope.settings,
        default='imagery:red,parallelism:blue',
    )
    source = String(
        display_name=_("Source/Citation"),
        help=_("Optional for citing source of any material used. Automatic citation can be done using <a href=\"http://easybib.com\">EasyBib</a>"),
        scope=Scope.settings,
        default='None',
    )
    diacritics = String(
        display_name=_("Diacritic Marks"),
        help=_("Add diacritic marks to be added to a text using the comma-separated form, i.e. markname;urltomark;baseline,markname2;urltomark2;baseline2"),
        scope=Scope.settings,
        default='',
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


class TextAnnotationModule(AnnotatableFields, XModule):
    ''' Text Annotation Module '''
    js = {'coffee': [],
          'js': []}
    css = {'scss': [resource_string(__name__, 'css/annotatable/display.scss')]}
    icon_class = 'textannotation'

    def __init__(self, *args, **kwargs):
        super(TextAnnotationModule, self).__init__(*args, **kwargs)

        xmltree = etree.fromstring(self.data)

        self.instructions = self._extract_instructions(xmltree)
        self.content = etree.tostring(xmltree, encoding='unicode')
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
            'course_key': self.runtime.course_id,
            'display_name': self.display_name_with_default,
            'tag': self.instructor_tags,
            'source': self.source,
            'instructions_html': self.instructions,
            'content_html': self.content,
            'token': retrieve_token(self.user_email, self.annotation_token_secret),
            'diacritic_marks': self.diacritics,
            'annotation_storage': self.annotation_storage_url,
            'default_tab': self.default_tab,
            'instructor_email': self.instructor_email,
            'annotation_mode': self.annotation_mode,
            'is_course_staff': self.is_course_staff,
        }
        fragment = Fragment(self.system.render_template('textannotation.html', context))

        # TinyMCE already exists in Studio so we should not load the files again
        # get_real_user always returns "None" in Studio since its runtimes contains no anonymous ids
        if self.runtime.get_real_user is not None:
            fragment.add_javascript_url(self.runtime.STATIC_URL + "js/vendor/tinymce/js/tinymce/tinymce.full.min.js")
            fragment.add_javascript_url(self.runtime.STATIC_URL + "js/vendor/tinymce/js/tinymce/jquery.tinymce.min.js")
        return fragment


class TextAnnotationDescriptor(AnnotatableFields, RawDescriptor):
    ''' Text Annotation Descriptor '''
    module_class = TextAnnotationModule
    mako_template = "widgets/raw-edit.html"

    @property
    def non_editable_metadata_fields(self):
        non_editable_fields = super(TextAnnotationDescriptor, self).non_editable_metadata_fields
        non_editable_fields.extend([
            TextAnnotationDescriptor.annotation_storage_url,
            TextAnnotationDescriptor.annotation_token_secret,
        ])
        return non_editable_fields
