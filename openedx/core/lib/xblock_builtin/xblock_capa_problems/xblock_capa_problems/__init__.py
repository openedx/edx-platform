# -*- coding: utf-8 -*-
"""
CAPA Problems XBlock
"""
import json
import logging
import re
import sys

from lxml import etree

from django.conf import settings
from django.core.cache import cache as django_cache
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from django.utils.translation import gettext_noop as _
from requests.auth import HTTPBasicAuth
from six import text_type
from webob import Response
from webob.multidict import MultiDict
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin

import static_replace
from capa import responsetypes
from capa.xqueue_interface import XQueueInterface
from openedx.core.lib.xblock_builtin import get_css_dependencies, get_js_dependencies
from student.models import anonymous_id_for_user
from xmodule.contentstore.django import contentstore
from xmodule.exceptions import NotFoundError, ProcessingError
from .capa_base import CapaFields, CapaMixin, ComplexEncoder
from xmodule.raw_module import RawDescriptor
from xmodule.xml_module import XmlParserMixin
from xmodule.util.misc import escape_html_characters
from xmodule.util.sandboxing import get_python_lib_zip, can_execute_unsafe_code


log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)  # pylint: disable=invalid-name


@XBlock.wants('user')
@XBlock.needs('i18n')
@XBlock.needs('request')
class CapaProblemsXBlock(XBlock, CapaFields, CapaMixin, StudioEditableXBlockMixin, XmlParserMixin):
    """
    An XBlock implementing LonCapa format problems, by way of
    capa.capa_problem.LoncapaProblem
    """
    INDEX_CONTENT_TYPE = 'CAPA'
    icon_class = 'problem'

    editable_fields = [
        "display_name",
        "max_attempts",
        "showanswer",
        "show_reset_button",
        "rerandomize",
        "data",
        "submission_wait_seconds",
        "weight",
        "source_code",
        "use_latex_compiler",
        "matlab_api_key",
    ]

    has_author_view = True

    # The capa format specifies that what we call max_attempts in the code
    # is the attribute `attempts`. This will do that conversion
    metadata_translations = dict(RawDescriptor.metadata_translations)
    metadata_translations['attempts'] = 'max_attempts'

    # TODO from CapaDescriptor
    '''
    resources_dir = None

    show_in_read_only_mode = True
    template_dir_name = 'problem'
    mako_template = "widgets/problem-edit.html"

    from pkg_resources import resource_string
    js = {'js': [resource_string(__name__, 'js/src/problem/edit.js')]}
    js_module_name = "MarkdownEditingDescriptor"
    css = {
        'scss': [
            resource_string(__name__, 'css/editor/edit.scss'),
        ]
    }

    @classmethod
    def filter_templates(cls, template, course):
        """
        Filter template that contains 'latex' from templates.

        Show them only if use_latex_compiler is set to True in
        course settings.
        """
        return 'latex' not in template['template_id'] or course.use_latex_compiler

    # VS[compat]
    # TODO (cpennington): Delete this method once all fall 2012 course are being
    # edited in the cms
    @classmethod
    def backcompat_paths(cls, path):
        import dogstats_wrapper as dog_stats_api
        from xmodule.x_module import DEPRECATION_VSCOMPAT_EVENT
        dog_stats_api.increment(
            DEPRECATION_VSCOMPAT_EVENT,
            tags=["location:capa_descriptor_backcompat_paths"]
        )
        return [
            'problems/' + path[8:],
            path[8:],
        ]

    def index_dictionary(self):
        """
        Return dictionary prepared with module content and type for indexing.
        """
        xblock_body = super(CapaDescriptor, self).index_dictionary()
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
            self.data
        )
        capa_content = escape_html_characters(capa_content)
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

    '''

    def student_view(self, context=None):  # pylint: disable=unused-argument
        """
        Return a fragment with the html from this XBlock

        Doesn't yet add any of the javascript to the fragment, nor the css.
        Also doesn't expect any javascript binding, yet.

        Makes no use of the context parameter
        """
        log.debug("CapaProblemsXBlock.student_view")
        self.load_state()

        fragment = Fragment()
        self.add_resource_urls(fragment)
        fragment.add_content(self.get_html())
        fragment.initialize_js('CapaProblemXBlock')
        return fragment

    def author_view(self, context=None):
        """
        Renders the Studio preview view.
        """
        log.debug("CapaProblemsXBlock.author_view")
        if context is None:
            context = {}
        context.update({
            'markdown': self.markdown,
            'enable_markdown': self.markdown is not None,
            'enable_latex_compiler': self.use_latex_compiler,
        })
        return self.student_view(context)

    @staticmethod
    def vendor_js_dependencies():
        """
        Returns list of vendor JS files that this XBlock depends on.
        """
        return get_js_dependencies('capa_vendor')

    @staticmethod
    def js_dependencies():
        """
        Returns list of JS files that this XBlock depends on.
        """
        return get_js_dependencies('capa')

    @staticmethod
    def css_dependencies():
        """
        Returns list of CSS files that this XBlock depends on.
        """
        return get_css_dependencies('style-capa')

    def add_resource_urls(self, fragment):
        """
        Adds URLs for JS and CSS resources that this XBlock depends on to `fragment`.
        """
        for vendor_js_file in self.vendor_js_dependencies():
            fragment.add_resource_url(staticfiles_storage.url(vendor_js_file), "application/javascript", "head")

        for css_file in self.css_dependencies():
            fragment.add_css_url(staticfiles_storage.url(css_file))

        # Body dependencies
        for js_file in self.js_dependencies():
            fragment.add_javascript_url(staticfiles_storage.url(js_file))

    @property
    def ajax_url(self):
        """
        The url to be used by to call into handle_ajax
        """
        return self.runtime.handler_url(self, 'xmodule_handler')

    @XBlock.handler
    def xmodule_handler(self, request, suffix=None):
        """
        XBlock handler that wraps `handle_ajax`
        """
        # TODO: copied from x_module.XModule: reimplement and simplify.
        # Do we need all the webob stuff?
        class FileObjForWebobFiles(object):
            """
            Turn Webob cgi.FieldStorage uploaded files into pure file objects.
            Webob represents uploaded files as cgi.FieldStorage objects, which
            have a .file attribute.  We wrap the FieldStorage object, delegating
            attribute access to the .file attribute.  But the files have no
            name, so we carry the FieldStorage .filename attribute as the .name.
            """
            def __init__(self, webob_file):
                self.file = webob_file.file
                self.name = webob_file.filename

            def __getattr__(self, name):
                return getattr(self.file, name)

        # WebOb requests have multiple entries for uploaded files.  handle_ajax
        # expects a single entry as a list.
        request_post = MultiDict(request.POST)
        for key in set(request.POST.iterkeys()):
            if hasattr(request.POST[key], "file"):
                request_post[key] = map(FileObjForWebobFiles, request.POST.getall(key))

        response_data = self.handle_ajax(suffix, request_post)
        return Response(response_data, content_type='application/json', charset='UTF-8')

    def handle_ajax(self, request, dispatch):
        """
        This is called by courseware.module_render, to handle an AJAX call.

        Returns a json dictionary:
        { 'progress_changed' : True/False,
          'progress' : 'none'/'in_progress'/'done',
          <other request-specific values here > }
        """
        # TODO: split these handlers into separate XBlock.handlers?
        log.debug("CapaProblemsXBlock.handle_ajax")
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
            result = handlers[dispatch](request.POST)

        except NotFoundError:
            log.info(
                "Unable to find data when dispatching %s to %s for user %s",
                dispatch,
                self.scope_ids.usage_id,
                self.scope_ids.user_id
            )
            _, _, traceback_obj = sys.exc_info()  # pylint: disable=redefined-outer-name
            raise ProcessingError(not_found_error_message), None, traceback_obj

        except Exception:
            log.exception(
                "Unknown error when dispatching %s to %s for user %s",
                dispatch,
                self.scope_ids.usage_id,
                self.scope_ids.user_id
            )
            _, _, traceback_obj = sys.exc_info()  # pylint: disable=redefined-outer-name
            raise ProcessingError(generic_error_message), None, traceback_obj

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
    def parse_xml(cls, node, runtime, keys, id_generator):
        """
        Parses OLX into XBlock.

        This method is overridden here to allow parsing legacy OLX, coming from CAPA XModule.
        XBlock stores all the associated data, fields and children in a XML element inlined into vertical XML file.
        """
        return 'latex' not in template['template_id'] or course.use_latex_compiler

    def get_context(self):
        _context = RawDescriptor.get_context(self)
        _context.update({
            'markdown': self.markdown,
            'enable_markdown': self.markdown is not None,
            'enable_latex_compiler': self.use_latex_compiler,
        })
        return _context

    @property
    def _user(self):
        """
        Returns the current user object.
        """
        user_service = self.runtime.service(self, 'user')
        return user_service._django_user if user_service else None

    @property
    def anonymous_student_id(self):
        """
        Returns the anonymous user ID for the current user+course.
        """
        user = self._user
        if user:
            return anonymous_id_for_user(user, self.runtime.course_id)
        else:
            return None

    @property
    def user_is_staff(self):
        """
        Returns true if the current user is a staff user.
        """
        user_service = self.runtime.service(self, 'user')
        return user_service.user_is_staff() if user_service else None

    @property
    def block_seed(self):
        """
        Returns the randomization seed.

        Uncertain why we need a block-level seed, when there is a user_state seed too?
        """
        user = self._user
        return user.id if user else 0

    @property
    def cache(self):
        """
        Returns the default django cache.
        """
        return django_cache

    @property
    def node_path(self):
        """Return the configured node path."""
        return settings.NODE_PATH

    @property
    def xqueue_interface(self):
        """
        Returns a dict containing XqueueInterface object, as well as parameters
        for the specific StudentModule.

        Copied from courseware.module_render.get_module_system_for_user
        """
        # TODO: refactor into common repo/code?

        def get_xqueue_callback_url_prefix(request):
            """
            Calculates default prefix based on request, but allows override via settings

            This is separated from get_module_for_descriptor so that it can be called
            by the LMS before submitting background tasks to run.  The xqueue callbacks
            should go back to the LMS, not to the worker.
            """
            prefix = '{proto}://{host}'.format(
                proto=request.META.get('HTTP_X_FORWARDED_PROTO', 'https' if request.is_secure() else 'http'),
                host=request.get_host()
            )
            return settings.XQUEUE_INTERFACE.get('callback_url', prefix)

        def make_xqueue_callback(dispatch='score_update'):
            """
            Returns fully qualified callback URL for external queueing system
            """
            relative_xqueue_callback_url = reverse(
                'xqueue_callback',
                kwargs=dict(
                    course_id=text_type(self.runtime.course_id),
                    userid=str(self._user.id),
                    mod_id=text_type(self.location),
                    dispatch=dispatch
                ),
            )
            xqueue_callback_url_prefix = get_xqueue_callback_url_prefix(self.runtime.request)
            return xqueue_callback_url_prefix + relative_xqueue_callback_url

        # Default queuename is course-specific and is derived from the course that
        #   contains the current module.
        # TODO: Queuename should be derived from 'course_settings.json' of each course
        xqueue_default_queuename = self.location.org + '-' + self.location.course

        if settings.XQUEUE_INTERFACE.get('basic_auth') is not None:
            requests_auth = HTTPBasicAuth(*settings.XQUEUE_INTERFACE['basic_auth'])
        else:
            requests_auth = None

        xqueue_interface = XQueueInterface(
            settings.XQUEUE_INTERFACE['url'],
            settings.XQUEUE_INTERFACE['django_auth'],
            requests_auth,
        )

        return {
            'interface': xqueue_interface,
            'construct_callback': make_xqueue_callback,
            'default_queuename': xqueue_default_queuename.replace(' ', '_'),
            'waittime': settings.XQUEUE_WAITTIME_BETWEEN_REQUESTS
        }

    def replace_static_urls(self, html):
        """
        Replace the static URLs in the given html content.
        """
        # TODO: Refactor CAPA rendering so we don't need this?
        return static_replace.replace_static_urls(
            text=html,
            data_directory=getattr(self, 'data_dir', None),
            course_id=self.runtime.course_id,
            static_asset_path=self.static_asset_path,
        )

    def replace_course_urls(self, html):
        """
        Replace the course URLs in the given html content.
        """
        # TODO: Refactor CAPA rendering so we don't need this?
        return static_replace.replace_course_urls(
            text=html,
            course_key=self.runtime.course_id
        )

    def replace_jump_to_id_urls(self, html):
        """
        Replace the course URLs in the given html content.
        """
        # TODO: Refactor CAPA rendering so we don't need this?
        course_id = self.runtime.course_id
        return static_replace.replace_jump_to_id_urls(
            text=html,
            course_id=course_id,
            jump_to_id_base_url=reverse('jump_to_id', kwargs={'course_id': text_type(course_id), 'module_id': ''})
        )

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

    def can_execute_unsafe_code(self):
        """Pass through to xmodule.util.sandboxing method."""
        return can_execute_unsafe_code(self.runtime.course_id)

    def get_python_lib_zip(self):
        """Pass through to xmodule.util.sandboxing method."""
        return get_python_lib_zip(contentstore, self.runtime.course_id)

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
        Return the problem's max score
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
        lcp = LoncapaProblem(
            problem_text=self.data,
            id=self.location.html_id(),
            capa_system=capa_system,
            capa_module=self,
            state={},
            seed=1,
            minimal_init=True,
        )
        return lcp.get_max_score()

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
            anonymous_student_id=self.anonymous_user_id,
            cache=None,
            can_execute_unsafe_code=lambda: None,
            get_python_lib_zip=self.get_python_lib_zip,
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
