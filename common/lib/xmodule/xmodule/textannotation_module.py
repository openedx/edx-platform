''' Text annotation module '''

import datetime
from django.http import (HttpResponse)
from lxml import etree
from pkg_resources import resource_string

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from xblock.core import Scope, String
from xmodule.firebase_token_generator import create_token

import textwrap


class AnnotatableFields(object):
    """Fields for `TextModule` and `TextDescriptor`."""
    data = String(help="XML data for the annotation", scope=Scope.content, default=textwrap.dedent("""\
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
        display_name="Display Name",
        help="Display name for this module",
        scope=Scope.settings,
        default='Text Annotation',
    )
    instructor_tags = String(
        display_name="Tags for Assignments",
        help="Add tags that automatically highlight in a certain color using the comma-separated form, i.e. imagery:red,parallelism:blue",
        scope=Scope.settings,
        default='imagery:red,parallelism:blue',
    )
    source = String(
        display_name="Source/Citation",
        help="Optional for citing source of any material used. Automatic citation can be done using <a href=\"http://easybib.com\">EasyBib</a>",
        scope=Scope.settings,
        default='None',
    )
    annotation_storage_url = String(help="Location of Annotation backend", scope=Scope.settings, default="http://your_annotation_storage.com", display_name="Url for Annotation Storage")
    diacritics = String(
        display_name="Diacritic Marks",
        help="Add diacritic marks to be added to a text using the comma-separated form, i.e. markname;urltomark;baseline,markname2;urltomark2;baseline2",
        scope=Scope.settings,
        default='',
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
            'tag': self.instructor_tags,
            'source': self.source,
            'instructions_html': self.instructions,
            'content_html': self.content,
            'annotation_storage': self.annotation_storage_url,
            'token': self.token(self.user),
            'diacritic_marks': self.diacritics,
        }
        return self.system.render_template('textannotation.html', context)


class TextAnnotationDescriptor(AnnotatableFields, RawDescriptor):
    ''' Text Annotation Descriptor '''
    module_class = TextAnnotationModule
    mako_template = "widgets/raw-edit.html"

    @property
    def non_editable_metadata_fields(self):
        non_editable_fields = super(TextAnnotationDescriptor, self).non_editable_metadata_fields
        non_editable_fields.extend([
            TextAnnotationDescriptor.annotation_storage_url
        ])
        return non_editable_fields
