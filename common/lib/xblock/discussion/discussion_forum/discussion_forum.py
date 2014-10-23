import logging

from xblock.core import XBlock
from xblock.fields import Scope, String
from xblock.fragment import Fragment

from .utils import (
    render_template,
    render_mako_template,
    render_mustache_templates,
    get_js_urls, get_css_urls,
    asset_to_static_url
)

log = logging.getLogger(__name__)


@XBlock.needs('discussion')
class DiscussionXBlock(XBlock):
    """ Provides functionality similar to discussion XModule in inline mode """
    display_name = String(
        display_name="Display Name",
        help="Display name for this module",
        default="Discussion",
        scope=Scope.settings
    )
    data = String(
        help="XML data for the problem",
        scope=Scope.content,
        default="<discussion></discussion>"
    )
    discussion_category = String(
        display_name="Category",
        default="Week 1",
        help="A category name for the discussion. This name appears in the left pane of the discussion forum for the course.",
        scope=Scope.settings
    )
    discussion_target = String(
        display_name="Subcategory",
        default="Topic-Level Student-Visible Label",
        help="A subcategory name for the discussion. This name appears in the left pane of the discussion forum for the course.",
        scope=Scope.settings
    )
    sort_key = String(scope=Scope.settings)

    @property
    def discussion_id(self):
        """
        :return: int discussion id
        """
        return self.scope_ids.usage_id.block_id

    @property
    def course_id(self):
        """
        :return: int course id
        """
        # TODO really implement this
        # pylint: disable=no-member
        if hasattr(self, 'xmodule_runtime'):
            if hasattr(self.xmodule_runtime.course_id, 'to_deprecated_string'):
                return self.xmodule_runtime.course_id.to_deprecated_string()
            else:
                return self.xmodule_runtime.course_id
        return 'foo'

    def student_view(self, context=None):  # pylint: disable=unused-argument
        """ Renders student view for LMS and Studio """
        # pylint: disable=no-member
        if hasattr(self, 'xmodule_runtime') and getattr(self.xmodule_runtime, 'is_author_mode', False):
            fragment = self._student_view_studio()
        else:
            fragment = self._student_view_lms()

        return fragment

    def _student_view_lms(self):
        """ Renders student view for LMS """
        fragment = Fragment()
        discussion_service = self.xmodule_runtime.service(self, 'discussion')  # pylint: disable=no-member
        context = discussion_service.get_inline_template_context(self.discussion_id)
        context['discussion_id'] = self.discussion_id

        fragment.add_content(render_mako_template('discussion/_discussion_inline.html', context))

        for url in get_js_urls():
            fragment.add_javascript_url(url)
        for url in get_css_urls():
            fragment.add_css_url(url)

        fragment.add_javascript(render_template('static/js/discussion_inline.js', {'course_id': self.course_id}))
        fragment.add_content(render_mustache_templates())

        fragment.initialize_js('DiscussionInlineBlock')

        return fragment

    def _student_view_studio(self):
        """ Renders student view for Studio """
        fragment = Fragment()
        fragment.add_content(render_mako_template(
            'discussion/_discussion_inline_studio.html',
            {'discussion_id': self.discussion_id}
        ))
        fragment.add_css_url(asset_to_static_url('xblock/discussion/css/discussion-studio.css'))
        return fragment

    @XBlock.json_handler
    def studio_submit(self, data, suffix=''):  # pylint: disable=unused-argument
        """ Handles Studio submit event """
        log.info("submitted: {}".format(data))
        self.display_name = data.get("display_name", "Untitled Discussion Topic")
        self.discussion_category = data.get("discussion_category", None)
        self.discussion_target = data.get("discussion_target", None)
        return {
            "display_name": self.display_name,
            "discussion_category": self.discussion_category,
            "discussion_target": self.discussion_target
        }

    def studio_view(self, context=None):  # pylint: disable=unused-argument
        """ Renders author view for Studio """
        fragment = Fragment()
        context = {
            "display_name": self.display_name,
            "discussion_category": self.discussion_category,
            "discussion_target": self.discussion_target
        }
        log.info("rendering template in context: {}".format(context))
        fragment.add_content(render_mako_template('discussion/discussion_inline_edit.html', context))
        fragment.add_javascript_url(asset_to_static_url('xblock/discussion/js/discussion_inline_edit.js'))

        fragment.initialize_js('DiscussionEditBlock')
        return fragment

    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("Discussion XBlock",
             """<vertical_demo>
                <discussion-forum/>
                </vertical_demo>
             """),
        ]


@XBlock.needs('discussion')
class DiscussionCourseXBlock(XBlock):
    """ Provides functionality similar to discussion XModule in tab mode """
    display_name = String(
        display_name="Display Name",
        help="Display name for this module",
        default="Discussion Course",
        scope=Scope.settings
    )

    def student_view(self, context=None):  # pylint: disable=unused-argument
        """ Renders student view for LMS and Studio """
        # pylint: disable=no-member
        if hasattr(self, 'xmodule_runtime') and getattr(self.xmodule_runtime, 'is_author_mode', False):
            fragment = self._student_view_studio()
        else:
            fragment = self._student_view_lms()

        return fragment

    def _student_view_lms(self):
        """ Renders student view for LMS """
        fragment = Fragment()
        fragment.add_css_url(asset_to_static_url('xblock/discussion/css/discussion-course-custom.css'))

        discussion_service = self.xmodule_runtime.service(self, 'discussion')  # pylint: disable=no-member
        context = discussion_service.get_course_template_context()
        context['enable_new_post_btn'] = True

        fragment.add_content(render_mako_template('discussion/_discussion_course.html', context))

        fragment.add_javascript(render_template('static/js/discussion_course.js', {
            'course_id': self.course_id
        }))

        fragment.add_content(render_mustache_templates())

        for url in get_js_urls():
            fragment.add_javascript_url(url)

        for url in get_css_urls():
            fragment.add_css_url(url)

        fragment.initialize_js('DiscussionCourseBlock')

        return fragment

    def _student_view_studio(self):
        """ Renders student view for Studio """
        fragment = Fragment()
        fragment.add_content(render_mako_template('discussion/_discussion_course_studio.html'))
        fragment.add_css_url(asset_to_static_url('xblock/discussion/css/discussion-studio.css'))
        return fragment

    def studio_view(self, context=None):  # pylint: disable=unused-argument
        """ Renders author view Studio """
        return Fragment()
