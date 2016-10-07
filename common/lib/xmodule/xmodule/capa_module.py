"""Implements basics of Capa, including class CapaModule."""
import json
import logging
import sys
import re
from lxml import etree

from pkg_resources import resource_string

import dogstats_wrapper as dog_stats_api
from .capa_base import CapaMixin, CapaFields, ComplexEncoder
from capa import responsetypes
from .progress import Progress
from xmodule.util.misc import escape_html_characters
from xmodule.x_module import XModule, module_attr, DEPRECATION_VSCOMPAT_EVENT
from xmodule.raw_module import RawDescriptor
from xmodule.exceptions import NotFoundError, ProcessingError

log = logging.getLogger("edx.courseware")


class CapaModule(CapaMixin, XModule):
    """
    An XModule implementing LonCapa format problems, implemented by way of
    capa.capa_problem.LoncapaProblem

    CapaModule.__init__ takes the same arguments as xmodule.x_module:XModule.__init__
    """
    icon_class = 'problem'

    js = {
        'coffee': [
            resource_string(__name__, 'js/src/capa/display.coffee'),
        ],
        'js': [
            resource_string(__name__, 'js/src/javascript_loader.js'),
            resource_string(__name__, 'js/src/collapsible.js'),
            resource_string(__name__, 'js/src/capa/imageinput.js'),
            resource_string(__name__, 'js/src/capa/schematic.js'),
        ]
    }

    js_module_name = "Problem"
    css = {'scss': [resource_string(__name__, 'css/capa/display.scss')]}

    def __init__(self, *args, **kwargs):
        """
        Accepts the same arguments as xmodule.x_module:XModule.__init__
        """
        super(CapaModule, self).__init__(*args, **kwargs)

    def author_view(self, context):
        """
        Renders the Studio preview view.
        """
        return self.student_view(context)

    def handle_ajax(self, dispatch, data):
        """
        This is called by courseware.module_render, to handle an AJAX call.

        `data` is request.POST.

        Returns a json dictionary:
        { 'progress_changed' : True/False,
          'progress' : 'none'/'in_progress'/'done',
          <other request-specific values here > }
        """
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

        try:
            result = handlers[dispatch](data)

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

        result.update({
            'progress_changed': after != before,
            'progress_status': Progress.to_js_status_str(after),
            'progress_detail': Progress.to_js_detail_str(after),
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


class CapaDescriptor(CapaFields, RawDescriptor):
    """
    Module implementing problems in the LON-CAPA format,
    as implemented by capa.capa_problem
    """
    INDEX_CONTENT_TYPE = 'CAPA'

    module_class = CapaModule
    resources_dir = None

    has_score = True
    show_in_read_only_mode = True
    template_dir_name = 'problem'
    mako_template = "widgets/problem-edit.html"
    js = {'coffee': [resource_string(__name__, 'js/src/problem/edit.coffee')]}
    js_module_name = "MarkdownEditingDescriptor"
    has_author_view = True
    css = {
        'scss': [
            resource_string(__name__, 'css/editor/edit.scss'),
            resource_string(__name__, 'css/problem/edit.scss')
        ]
    }

    # The capa format specifies that what we call max_attempts in the code
    # is the attribute `attempts`. This will do that conversion
    metadata_translations = dict(RawDescriptor.metadata_translations)
    metadata_translations['attempts'] = 'max_attempts'

    @classmethod
    def filter_templates(cls, template, course):
        """
        Filter template that contains 'latex' from templates.

        Show them only if use_latex_compiler is set to True in
        course settings.
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

    # VS[compat]
    # TODO (cpennington): Delete this method once all fall 2012 course are being
    # edited in the cms
    @classmethod
    def backcompat_paths(cls, path):
        dog_stats_api.increment(
            DEPRECATION_VSCOMPAT_EVENT,
            tags=["location:capa_descriptor_backcompat_paths"]
        )
        return [
            'problems/' + path[8:],
            path[8:],
        ]

    @property
    def non_editable_metadata_fields(self):
        non_editable_fields = super(CapaDescriptor, self).non_editable_metadata_fields
        non_editable_fields.extend([
            CapaDescriptor.due,
            CapaDescriptor.graceperiod,
            CapaDescriptor.force_save_button,
            CapaDescriptor.markdown,
            CapaDescriptor.use_latex_compiler,
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

    # Proxy to CapaModule for access to any of its attributes
    answer_available = module_attr('answer_available')
    submit_button_name = module_attr('submit_button_name')
    submit_button_submitting_name = module_attr('submit_button_submitting_name')
    submit_problem = module_attr('submit_problem')
    choose_new_seed = module_attr('choose_new_seed')
    closed = module_attr('closed')
    get_answer = module_attr('get_answer')
    get_problem = module_attr('get_problem')
    get_problem_html = module_attr('get_problem_html')
    get_state_for_lcp = module_attr('get_state_for_lcp')
    handle_input_ajax = module_attr('handle_input_ajax')
    hint_button = module_attr('hint_button')
    handle_problem_html_error = module_attr('handle_problem_html_error')
    handle_ungraded_response = module_attr('handle_ungraded_response')
    is_attempted = module_attr('is_attempted')
    is_correct = module_attr('is_correct')
    is_past_due = module_attr('is_past_due')
    is_submitted = module_attr('is_submitted')
    lcp = module_attr('lcp')
    make_dict_of_responses = module_attr('make_dict_of_responses')
    new_lcp = module_attr('new_lcp')
    publish_grade = module_attr('publish_grade')
    rescore_problem = module_attr('rescore_problem')
    reset_problem = module_attr('reset_problem')
    save_problem = module_attr('save_problem')
    set_state_from_lcp = module_attr('set_state_from_lcp')
    should_show_submit_button = module_attr('should_show_submit_button')
    should_show_reset_button = module_attr('should_show_reset_button')
    should_show_save_button = module_attr('should_show_save_button')
    update_score = module_attr('update_score')
