"""Implements basics of Capa, including class CapaModule."""


import json
import logging
import re
import sys

import six
from bleach.sanitizer import Cleaner
from lxml import etree
from pkg_resources import resource_string
from web_fragments.fragment import Fragment
from xblock.core import XBlock

from capa import responsetypes
from xmodule.contentstore.django import contentstore
from xmodule.editing_module import EditingMixin
from xmodule.exceptions import NotFoundError, ProcessingError
from xmodule.raw_module import RawMixin
from xmodule.util.sandboxing import get_python_lib_zip
from xmodule.util.xmodule_django import add_webpack_to_fragment
from xmodule.x_module import (
    HTMLSnippet,
    ResourceTemplates,
    XModuleDescriptorToXBlockMixin,
    XModuleMixin,
    XModuleToXBlockMixin,
    shim_xmodule_js
)
from xmodule.xml_module import XmlMixin

from .capa_base import CapaMixin, ComplexEncoder, _

log = logging.getLogger("edx.courseware")


@XBlock.wants('user')
@XBlock.needs('i18n')
@XBlock.wants('call_to_action')
class ProblemBlock(
        CapaMixin, RawMixin, XmlMixin, EditingMixin,
        XModuleDescriptorToXBlockMixin, XModuleToXBlockMixin, HTMLSnippet, ResourceTemplates, XModuleMixin):
    """
    The XBlock for CAPA.
    """
    INDEX_CONTENT_TYPE = 'CAPA'

    resources_dir = None

    has_score = True
    show_in_read_only_mode = True
    template_dir_name = 'problem'
    mako_template = "widgets/problem-edit.html"
    has_author_view = True

    # The capa format specifies that what we call max_attempts in the code
    # is the attribute `attempts`. This will do that conversion
    metadata_translations = dict(XmlMixin.metadata_translations)
    metadata_translations['attempts'] = 'max_attempts'

    icon_class = 'problem'

    uses_xmodule_styles_setup = True
    requires_per_student_anonymous_id = True

    preview_view_js = {
        'js': [
            resource_string(__name__, 'js/src/javascript_loader.js'),
            resource_string(__name__, 'js/src/capa/display.js'),
            resource_string(__name__, 'js/src/collapsible.js'),
            resource_string(__name__, 'js/src/capa/imageinput.js'),
            resource_string(__name__, 'js/src/capa/schematic.js'),
        ],
        'xmodule_js': resource_string(__name__, 'js/src/xmodule.js')
    }

    preview_view_css = {
        'scss': [
            resource_string(__name__, 'css/capa/display.scss'),
        ],
    }

    studio_view_js = {
        'js': [
            resource_string(__name__, 'js/src/problem/edit.js'),
        ],
        'xmodule_js': resource_string(__name__, 'js/src/xmodule.js'),
    }

    studio_view_css = {
        'scss': [
            resource_string(__name__, 'css/editor/edit.scss'),
            resource_string(__name__, 'css/problem/edit.scss'),
        ]
    }

    def bind_for_student(self, *args, **kwargs):
        super(ProblemBlock, self).bind_for_student(*args, **kwargs)

        # Capa was an XModule. When bind_for_student() was called on it with a new runtime, a new CapaModule object
        # was initialized when XModuleDescriptor._xmodule() was called next. self.lcp was constructed in CapaModule
        # init(). To keep the same behaviour, we delete self.lcp in bind_for_student().
        if 'lcp' in self.__dict__:
            del self.__dict__['lcp']

    def student_view(self, _context, show_detailed_errors=False):
        """
        Return the student view.
        """
        # self.score is initialized in self.lcp but in this method is accessed before self.lcp so just call it first.
        try:
            self.lcp
        except Exception as err:
            html = self.handle_fatal_lcp_error(err if show_detailed_errors else None)
        else:
            html = self.get_html()
        fragment = Fragment(html)
        add_webpack_to_fragment(fragment, 'ProblemBlockPreview')
        shim_xmodule_js(fragment, 'Problem')
        return fragment

    def public_view(self, context):
        """
        Return the view seen by users who aren't logged in or who aren't
        enrolled in the course.
        """
        if getattr(self.runtime, 'suppports_state_for_anonymous_users', False):
            # The new XBlock runtime can generally support capa problems for users who aren't logged in, so show the
            # normal student_view. To prevent anonymous users from viewing specific problems, adjust course policies
            # and/or content groups.
            return self.student_view(context)
        else:
            # Show a message that this content requires users to login/enroll.
            return super(ProblemBlock, self).public_view(context)

    def author_view(self, context):
        """
        Renders the Studio preview view.
        """
        return self.student_view(context, show_detailed_errors=True)

    def studio_view(self, _context):
        """
        Return the studio view.
        """
        fragment = Fragment(
            self.system.render_template(self.mako_template, self.get_context())
        )
        add_webpack_to_fragment(fragment, 'ProblemBlockStudio')
        shim_xmodule_js(fragment, 'MarkdownEditingDescriptor')
        return fragment

    def handle_ajax(self, dispatch, data):
        """
        This is called by courseware.module_render, to handle an AJAX call.

        `data` is request.POST.

        Returns a json dictionary:
        { 'progress_changed' : True/False,
          'progress' : 'none'/'in_progress'/'done',
          <other request-specific values here > }
        """
        # self.score is initialized in self.lcp but in this method is accessed before self.lcp so just call it first.
        self.lcp
        handlers = {
            'hint_button': self.hint_button,
            'problem_get': self.get_problem,
            'problem_check': self.submit_problem,
            'problem_reset': self.reset_problem,
            'problem_save': self.save_problem,
            'problem_show': self.get_answer,
            'score_update': self.update_score,
            'input_ajax': self.handle_input_ajax,
            'ungraded_response': self.handle_ungraded_response
        }

        _ = self.runtime.service(self, "i18n").ugettext

        generic_error_message = _(
            "We're sorry, there was an error with processing your request. "
            "Please try reloading your page and trying again."
        )

        not_found_error_message = _(
            "The state of this problem has changed since you loaded this page. "
            "Please refresh your page."
        )

        if dispatch not in handlers:
            return 'Error: {} is not a known capa action'.format(dispatch)

        before = self.get_progress()
        before_attempts = self.attempts

        try:
            result = handlers[dispatch](data)

        except NotFoundError:
            log.info(
                "Unable to find data when dispatching %s to %s for user %s",
                dispatch,
                self.scope_ids.usage_id,
                self.scope_ids.user_id
            )
            _, _, traceback_obj = sys.exc_info()
            six.reraise(ProcessingError, ProcessingError(not_found_error_message), traceback_obj)

        except Exception:
            log.exception(
                "Unknown error when dispatching %s to %s for user %s",
                dispatch,
                self.scope_ids.usage_id,
                self.scope_ids.user_id
            )
            _, _, traceback_obj = sys.exc_info()
            six.reraise(ProcessingError, ProcessingError(generic_error_message), traceback_obj)

        after = self.get_progress()
        after_attempts = self.attempts
        progress_changed = (after != before) or (after_attempts != before_attempts)
        curr_score, total_possible = self.get_display_progress()

        result.update({
            'progress_changed': progress_changed,
            'current_score': curr_score,
            'total_possible': total_possible,
            'attempts_used': after_attempts,
        })

        return json.dumps(result, cls=ComplexEncoder)

    @property
    def display_name_with_default(self):
        """
        Constructs the display name for a CAPA problem.

        Default to the display_name if it isn't None or not an empty string,
        else fall back to problem category.
        """
        if self.display_name is None or not self.display_name.strip():
            return self.location.block_type

        return self.display_name

    @classmethod
    def filter_templates(cls, template, course):
        """
        Filter template that contains 'latex' from templates.

        Show them only if use_latex_compiler is set to True in
        course settings.
        """
        return 'latex' not in template['template_id'] or course.use_latex_compiler

    def get_context(self):
        _context = EditingMixin.get_context(self)
        _context.update({
            'markdown': self.markdown,
            'enable_markdown': self.markdown is not None,
            'enable_latex_compiler': self.use_latex_compiler,
        })
        return _context

    # VS[compat]
    # TODO (cpennington): Delete this method once all fall 2012 course are being
    # edited in the cms
    @classmethod
    def backcompat_paths(cls, path):
        return [
            'problems/' + path[8:],
            path[8:],
        ]

    @property
    def non_editable_metadata_fields(self):
        non_editable_fields = super(ProblemBlock, self).non_editable_metadata_fields
        non_editable_fields.extend([
            ProblemBlock.due,
            ProblemBlock.graceperiod,
            ProblemBlock.force_save_button,
            ProblemBlock.markdown,
            ProblemBlock.use_latex_compiler,
            ProblemBlock.show_correctness,
        ])
        return non_editable_fields

    @property
    def problem_types(self):
        """ Low-level problem type introspection for content libraries filtering by problem type """
        try:
            tree = etree.XML(self.data)
        except etree.XMLSyntaxError:
            log.error('Error parsing problem types from xml for capa module {}'.format(self.display_name))
            return None  # short-term fix to prevent errors (TNL-5057). Will be more properly addressed in TNL-4525.
        registered_tags = responsetypes.registry.registered_tags()
        return {node.tag for node in tree.iter() if node.tag in registered_tags}

    def index_dictionary(self):
        """
        Return dictionary prepared with module content and type for indexing.
        """
        xblock_body = super(ProblemBlock, self).index_dictionary()

        # Make optioninput's options index friendly by replacing the actual tag with the values
        capa_content = re.sub(r'<optioninput options="\(([^"]+)\)".*?>\s*|\S*<\/optioninput>', r'\1', self.data)

        # Removing solutions and hints, as well as script and style
        capa_content = re.sub(
            re.compile(
                r"""
                    <solution>.*?</solution> |
                    <script>.*?</script> |
                    <style>.*?</style> |
                    <[a-z]*hint.*?>.*?</[a-z]*hint>
                """,
                re.DOTALL |
                re.VERBOSE),
            "",
            capa_content
        )
        capa_content = re.sub(
            r"(\s|&nbsp;|//)+",
            " ",
            Cleaner(tags=[], strip=True).clean(capa_content)
        )

        capa_body = {
            "capa_content": capa_content,
            "display_name": self.display_name,
        }
        if "content" in xblock_body:
            xblock_body["content"].update(capa_body)
        else:
            xblock_body["content"] = capa_body
        xblock_body["content_type"] = self.INDEX_CONTENT_TYPE
        xblock_body["problem_types"] = list(self.problem_types)
        return xblock_body

    def has_support(self, view, functionality):
        """
        Override the XBlock.has_support method to return appropriate
        value for the multi-device functionality.
        Returns whether the given view has support for the given functionality.
        """
        if functionality == "multi_device":
            types = self.problem_types  # Avoid calculating this property twice
            return types is not None and all(
                responsetypes.registry.get_class_for_tag(tag).multi_device_support
                for tag in types
            )
        return False

    def max_score(self):
        """
        Return the problem's max score if problem is instantiated successfully, else return max score of 0.
        """
        from capa.capa_problem import LoncapaProblem, LoncapaSystem
        capa_system = LoncapaSystem(
            ajax_url=None,
            anonymous_student_id=None,
            cache=None,
            can_execute_unsafe_code=None,
            get_python_lib_zip=None,
            DEBUG=None,
            filestore=self.runtime.resources_fs,
            i18n=self.runtime.service(self, "i18n"),
            node_path=None,
            render_template=None,
            seed=None,
            STATIC_URL=None,
            xqueue=None,
            matlab_api_key=None,
        )
        try:
            lcp = LoncapaProblem(
                problem_text=self.data,
                id=self.location.html_id(),
                capa_system=capa_system,
                capa_module=self,
                state={},
                seed=1,
                minimal_init=True,
            )
        except responsetypes.LoncapaProblemError:
            log.exception(u"LcpFatalError for block {} while getting max score".format(str(self.location)))
            maximum_score = 0
        else:
            maximum_score = lcp.get_max_score()
        return maximum_score

    def generate_report_data(self, user_state_iterator, limit_responses=None):
        """
        Return a list of student responses to this block in a readable way.

        Arguments:
            user_state_iterator: iterator over UserStateClient objects.
                E.g. the result of user_state_client.iter_all_for_block(block_key)

            limit_responses (int|None): maximum number of responses to include.
                Set to None (default) to include all.

        Returns:
            each call returns a tuple like:
            ("username", {
                           "Question": "2 + 2 equals how many?",
                           "Answer": "Four",
                           "Answer ID": "98e6a8e915904d5389821a94e48babcf_10_1"
            })
        """

        from capa.capa_problem import LoncapaProblem, LoncapaSystem

        if self.category != 'problem':
            raise NotImplementedError()

        if limit_responses == 0:
            # Don't even start collecting answers
            return
        capa_system = LoncapaSystem(
            ajax_url=None,
            # TODO set anonymous_student_id to the anonymous ID of the user which answered each problem
            # Anonymous ID is required for Matlab, CodeResponse, and some custom problems that include
            # '$anonymous_student_id' in their XML.
            # For the purposes of this report, we don't need to support those use cases.
            anonymous_student_id=None,
            cache=None,
            can_execute_unsafe_code=lambda: None,
            get_python_lib_zip=(lambda: get_python_lib_zip(contentstore, self.runtime.course_id)),
            DEBUG=None,
            filestore=self.runtime.resources_fs,
            i18n=self.runtime.service(self, "i18n"),
            node_path=None,
            render_template=None,
            seed=1,
            STATIC_URL=None,
            xqueue=None,
            matlab_api_key=None,
        )
        _ = capa_system.i18n.ugettext

        count = 0
        for user_state in user_state_iterator:

            if 'student_answers' not in user_state.state:
                continue

            lcp = LoncapaProblem(
                problem_text=self.data,
                id=self.location.html_id(),
                capa_system=capa_system,
                # We choose to run without a fully initialized CapaModule
                capa_module=None,
                state={
                    'done': user_state.state.get('done'),
                    'correct_map': user_state.state.get('correct_map'),
                    'student_answers': user_state.state.get('student_answers'),
                    'has_saved_answers': user_state.state.get('has_saved_answers'),
                    'input_state': user_state.state.get('input_state'),
                    'seed': user_state.state.get('seed'),
                },
                seed=user_state.state.get('seed'),
                # extract_tree=False allows us to work without a fully initialized CapaModule
                # We'll still be able to find particular data in the XML when we need it
                extract_tree=False,
            )

            for answer_id, orig_answers in lcp.student_answers.items():
                # Some types of problems have data in lcp.student_answers that isn't in lcp.problem_data.
                # E.g. formulae do this to store the MathML version of the answer.
                # We exclude these rows from the report because we only need the text-only answer.
                if answer_id.endswith('_dynamath'):
                    continue

                if limit_responses and count >= limit_responses:
                    # End the iterator here
                    return

                question_text = lcp.find_question_label(answer_id)
                answer_text = lcp.find_answer_text(answer_id, current_answer=orig_answers)
                correct_answer_text = lcp.find_correct_answer_text(answer_id)

                count += 1
                report = {
                    _("Answer ID"): answer_id,
                    _("Question"): question_text,
                    _("Answer"): answer_text,
                }
                if correct_answer_text is not None:
                    report[_("Correct Answer")] = correct_answer_text
                yield (user_state.username, report)
