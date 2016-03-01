import copy
from datetime import datetime
from fs.errors import ResourceNotFoundError
import logging
from lxml import etree
import os
from path import Path as path
from pkg_resources import resource_string
import re
import sys
import textwrap

import dogstats_wrapper as dog_stats_api
from xmodule.util.misc import escape_html_characters
from xmodule.contentstore.content import StaticContent
from xmodule.editing_module import EditingDescriptor
from xmodule.edxnotes_utils import edxnotes
from xmodule.mako_module import MakoTemplateBlockBase
from xmodule.studio_editable import StudioEditableBlock
from xmodule.xml_module import XmlParserMixin
from xmodule.x_module import XModuleFields
from xmodule.html_checker import check_html
from xmodule.stringify import stringify_children
from xmodule.x_module import XModule, DEPRECATION_VSCOMPAT_EVENT
from xmodule.xml_module import XmlDescriptor, name_to_pathname
from xblock.core import XBlock
from xblock.fields import Scope, String, Boolean, List
from xblock.fragment import Fragment

log = logging.getLogger("edx.courseware")

# Make '_' a no-op so we can scrape strings. Using lambda instead of
#  `django.utils.translation.ugettext_noop` because Django cannot be imported in this file
_ = lambda text: text

class HtmlBlock(XModuleFields, StudioEditableBlock, XmlParserMixin, MakoTemplateBlockBase, XBlock):
    """
    This will eventually subclass XBlock and merge HtmlModule and HtmlDescriptor
    into one. For now, it's a place to put the pieces that are already sharable
    between the two (field information and XBlock handlers).
    """
    js_module_name = "HTMLModule"
    mako_template = "widgets/html-edit.html"
    show_in_read_only_mode = True

    display_name = String(
        display_name=_("Display Name"),
        help=_("This name appears in the horizontal navigation at the top of the page."),
        scope=Scope.settings,
        # it'd be nice to have a useful default but it screws up other things; so,
        # use display_name_with_default for those
        default=_("Text")
    )
    data = String(help=_(u"Html contents to display for this module"), default=u"Data string!", scope=Scope.content)
    source_code = String(
        help=_(u"Source code for LaTeX documents. This feature is not well-supported."),
        scope=Scope.settings
    )
    use_latex_compiler = Boolean(
        help=_("Enable LaTeX templates?"),
        default=False,
        scope=Scope.settings
    )
    editor = String(
        help=_(
            "Select Visual to enter content and have the editor automatically create the HTML. Select Raw to edit "
            "HTML directly. If you change this setting, you must save the component and then re-open it for editing."
        ),
        display_name=_("Editor"),
        default="visual",
        values=[
            {"display_name": _("Visual"), "value": "visual"},
            {"display_name": _("Raw"), "value": "raw"}
        ],
        scope=Scope.settings
    )

    @XBlock.supports("multi_device")
    def student_view(self, context):
        """
        Return a fragment that contains the html for the student view
        """
        data = self.data
        if self.runtime.anonymous_student_id:
            data = data.replace("%%USER_ID%%", self.runtime.anonymous_student_id)

        response_fragment = Fragment(unicode(data))
        response_fragment.add_javascript_url(self.runtime.local_resource_url(self, 'js/src/javascript_loader.coffee'))
        response_fragment.add_javascript_url(self.runtime.local_resource_url(self, 'js/src/html/display.coffee'))

        response_fragment.add_javascript_url(self.runtime.local_resource_url(self, 'js/src/collapsible.js'))
        response_fragment.add_javascript_url(self.runtime.local_resource_url(self, 'js/src/html/imageModal.js'))
        response_fragment.add_javascript_url(self.runtime.local_resource_url(self, 'js/common_static/js/vendor/draggabilly.pkgd.js'))

        response_fragment.add_css_url(self.runtime.local_resource_url(self, 'css/html/display.scss'))

        return response_fragment

    def studio_view(self, context):
        fragment = super(HtmlBlock, self).studio_view(context)
        return fragment

    author_view = student_view

    ###############################################################################################################
    ### HTMLDescriptor implemenation / consolidation with XBlock
    ###############################################################################################################

    @classmethod
    def filter_templates(cls, template, course):
        """
        Filter template that contains 'latex' from templates.

        Show them only if use_latex_compiler is set to True in
        course settings.
        """
        return 'latex' not in template['template_id'] or course.use_latex_compiler

    def get_context(self):
        """
        an override to add in specific rendering context, in this case we need to
        add in a base path to our c4x content addressing scheme
        """
        _context = EditingDescriptor.get_context(self)
        # Add some specific HTML rendering context when editing HTML modules where we pass
        # the root /c4x/ url for assets. This allows client-side substitutions to occur.
        _context.update({
            'base_asset_url': StaticContent.get_base_url_path_for_course_assets(self.location.course_key),
            'enable_latex_compiler': self.use_latex_compiler,
            'editor': self.editor
        })
        return _context

    # NOTE: html descriptors are special.  We do not want to parse and
    # export them ourselves, because that can break things (e.g. lxml
    # adds body tags when it exports, but they should just be html
    # snippets that will be included in the middle of pages.

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        '''Load a descriptor from the specified xml_object:

        If there is a filename attribute, load it as a string, and
        log a warning if it is not parseable by etree.HTMLParser.

        If there is not a filename attribute, the definition is the body
        of the xml_object, without the root tag (do not want <html> in the
        middle of a page)

        Args:
            xml_object: an lxml.etree._Element containing the definition to load
            system: the modulestore system or runtime which caches data
        '''
        filename = xml_object.get('filename')
        if filename is None:
            definition_xml = copy.deepcopy(xml_object)
            cls.clean_metadata_from_xml(definition_xml)
            return {'data': stringify_children(definition_xml)}, []
        else:
            # html is special.  cls.filename_extension is 'xml', but
            # if 'filename' is in the definition, that means to load
            # from .html
            # 'filename' in html pointers is a relative path
            # (not same as 'html/blah.html' when the pointer is in a directory itself)
            pointer_path = "{category}/{url_path}".format(
                category='html',
                url_path=name_to_pathname(location.name)
            )
            base = path(pointer_path).dirname()
            # log.debug("base = {0}, base.dirname={1}, filename={2}".format(base, base.dirname(), filename))
            filepath = "{base}/{name}.html".format(base=base, name=filename)
            # log.debug("looking for html file for {0} at {1}".format(location, filepath))

            # VS[compat]
            # TODO (cpennington): If the file doesn't exist at the right path,
            # give the class a chance to fix it up. The file will be written out
            # again in the correct format.  This should go away once the CMS is
            # online and has imported all current (fall 2012) courses from xml
            if not system.resources_fs.exists(filepath):

                dog_stats_api.increment(
                    DEPRECATION_VSCOMPAT_EVENT,
                    tags=["location:html_descriptor_load_definition"]
                )

                candidates = cls.backcompat_paths(filepath)
                # log.debug("candidates = {0}".format(candidates))
                for candidate in candidates:
                    if system.resources_fs.exists(candidate):
                        filepath = candidate
                        break

            try:
                with system.resources_fs.open(filepath) as infile:
                    html = infile.read().decode('utf-8')
                    # Log a warning if we can't parse the file, but don't error
                    if not check_html(html) and len(html) > 0:
                        msg = "Couldn't parse html in {0}, content = {1}".format(filepath, html)
                        log.warning(msg)
                        system.error_tracker("Warning: " + msg)

                    definition = {'data': html}

                    # TODO (ichuang): remove this after migration
                    # for Fall 2012 LMS migration: keep filename (and unmangled filename)
                    definition['filename'] = [filepath, filename]

                    return definition, []

            except (ResourceNotFoundError) as err:
                msg = 'Unable to load file contents at path {0}: {1} '.format(
                    filepath, err)
                # add more info and re-raise
                raise Exception(msg), None, sys.exc_info()[2]

    # TODO (vshnayder): make export put things in the right places.

    def definition_to_xml(self, resource_fs):
        ''' Write <html filename="" [meta-attrs="..."]> to filename.xml, and the html
        string to filename.html.
        '''

        # Write html to file, return an empty tag
        pathname = name_to_pathname(self.url_name)
        filepath = u'{category}/{pathname}.html'.format(
            category=self.category,
            pathname=pathname
        )

        resource_fs.makedir(os.path.dirname(filepath), recursive=True, allow_recreate=True)
        with resource_fs.open(filepath, 'w') as filestream:
            html_data = self.data.encode('utf-8')
            filestream.write(html_data)

        # write out the relative name
        relname = path(pathname).basename()

        elt = etree.Element('html')
        elt.set("filename", relname)
        return elt

    @property
    def non_editable_metadata_fields(self):
        """
        `use_latex_compiler` should not be editable in the Studio settings editor.
        """
        non_editable_fields = super(HtmlBlock, self).non_editable_metadata_fields
        non_editable_fields.append(HtmlBlock.use_latex_compiler)
        return non_editable_fields

    def index_dictionary(self):
        xblock_body = super(HtmlBlock, self).index_dictionary()
        # Removing script and style
        html_content = re.sub(
            re.compile(
                r"""
                    <script>.*?</script> |
                    <style>.*?</style>
                """,
                re.DOTALL |
                re.VERBOSE),
            "",
            self.data
        )
        html_content = escape_html_characters(html_content)
        html_body = {
            "html_content": html_content,
            "display_name": self.display_name,
        }
        if "content" in xblock_body:
            xblock_body["content"].update(html_body)
        else:
            xblock_body["content"] = html_body
        xblock_body["content_type"] = "Text"
        return xblock_body

###############################################################################################################
### Carrying over the Blocks that inherit from HtmlBlock.
###############################################################################################################


class AboutFields(XBlock):
    display_name = String(
        help=_("Display name for this module"),
        scope=Scope.settings,
        default="overview",
    )
    data = String(
        help=_("Html contents to display for this module"),
        default=u"",
        scope=Scope.content
    )

@XBlock.tag("detached")
class AboutBlock(AboutFields, HtmlBlock):
    """
    Overriding defaults but otherwise treated as HtmlBlock.
    """
    template_dir_name = "about"


class StaticTabFields(XBlock):
    display_name = String(
        display_name=_("Display Name"),
        help=_("This name appears in the horizontal navigation at the top of the page."),
        scope=Scope.settings,
        default="Empty",
    )
    data = String(
        default=textwrap.dedent(u"""\
            <p>Add the content you want students to see on this page.</p>
        """),
        scope=Scope.content,
        help=_("HTML for the additional pages")
    )

@XBlock.tag("detached")
class StaticTabBlock(StaticTabFields, HtmlBlock):
    """
    These pieces of course content are treated as HtmlModules but we need to overload where the templates are located
    in order to be able to create new ones
    """
    template_dir_name = None


class CourseInfoFields(XBlock):
    """
    Field overrides
    """
    items = List(
        help=_("List of course update items"),
        default=[],
        scope=Scope.content
    )
    data = String(
        help=_("Html contents to display for this module"),
        default=u"<ol></ol>",
        scope=Scope.content
    )

@XBlock.tag("detached")
class CourseInfoBlock(CourseInfoFields, HtmlBlock):
    """
    Just to support xblock field overrides
    """
    template_dir_name = None

    # statuses
    STATUS_VISIBLE = 'visible'
    STATUS_DELETED = 'deleted'
    TEMPLATE_DIR = 'courseware'

    @XBlock.supports("multi_device")
    def student_view(self, context):
        """ Returns html required for rendering XModule. """

        # When we switch this to an XBlock, we can merge this with student_view,
        # but for now the XModule mixin requires that this method be defined.
        # pylint: disable=no-member
        if self.data != "":
            if self.runtime.anonymous_student_id:
                return Fragment(self.data.replace("%%USER_ID%%", self.runtime.anonymous_student_id))
            return Fragment(self.data)
        else:
            course_updates = [item for item in self.items if item.get('status') == self.STATUS_VISIBLE]
            course_updates.sort(key=lambda item: datetime.strptime(item['date'], '%B %d, %Y'), reverse=True)

            context = {
                'visible_updates': course_updates[:3],
                'hidden_updates': course_updates[3:],
            }

            return Fragment(self.runtime.render_template("{0}/course_updates.html".format(self.TEMPLATE_DIR), context))