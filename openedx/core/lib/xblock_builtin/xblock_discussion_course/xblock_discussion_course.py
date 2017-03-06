# -*- coding: utf-8 -*-
"""
Course Discussion XBlock
"""
import logging

from django.templatetags.static import static

from xblockutils.resources import ResourceLoader

from xblock.core import XBlock
from xblock.fields import Scope, String
from xblock.fragment import Fragment

from openedx.core.lib.xblock_builtin.xblock_discussion_course.utils import (
    _, get_js_dependencies, render_mustache_templates
)


log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)  # pylint: disable=invalid-name


@XBlock.needs('discussion')
class DiscussionCourseXBlock(XBlock):
    """ Provides functionality similar to discussion XModule in tab mode """
    display_name = String(
        display_name=_("Display Name"),
        help=_("Display name for this module"),
        default=_("Discussion Course"),
        scope=Scope.settings
    )

    @staticmethod
    def vendor_js_dependencies():
        """
        Returns list of vendor JS files that this XBlock depends on.
        """
        return get_js_dependencies('discussion_vendor') + ['js/vendor/mustache.js']

    @staticmethod
    def js_dependencies():
        """
        Returns list of JS files that this XBlock depends on.
        """
        return get_js_dependencies('discussion')

    @staticmethod
    def css_dependencies():
        """
        Returns list of CSS files that this XBlock depends on.
        """
        return ['css/discussion/lms-discussion-main.css', 'xblock/discussion/css/discussion-course-custom.css']

    def add_resource_urls(self, fragment):
        """
        Adds URLs for JS and CSS resources that this XBlock depends on to `fragment`.
        """
        for vendor_js_file in self.vendor_js_dependencies():
            fragment.add_resource_url(static(vendor_js_file), "application/javascript", "head")

        for css_file in self.css_dependencies():
            fragment.add_css_url(static(css_file))

        for js_file in self.js_dependencies():
            fragment.add_javascript_url(static(js_file))

        fragment.add_javascript(loader.load_unicode("static/js/discussion_classes.js"))

        fragment.add_javascript_url(static('js/discussion_forum.js'))

        fragment.add_javascript(loader.render_template('static/js/discussion_course.js', {
            'course_id': self.course_id
        }))

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

        self.add_resource_urls(fragment)

        discussion_service = self.xmodule_runtime.service(self, 'discussion')  # pylint: disable=no-member
        context = discussion_service.get_course_template_context()
        context['enable_new_post_btn'] = True

        fragment.add_content(self.runtime.render_template('discussion/_discussion_course.html', context))

        fragment.add_content(render_mustache_templates())

        fragment.initialize_js('DiscussionCourseBlock')

        return fragment

    def _student_view_studio(self):
        """ Renders student view for Studio """
        fragment = Fragment()
        context = None
        fragment.add_content(self.runtime.render_template('discussion/_discussion_course_studio.html', context))
        fragment.add_css_url(static('xblock/discussion/css/discussion-studio.css'))
        return fragment

    def studio_view(self, context=None):  # pylint: disable=unused-argument
        """ Renders author view Studio """
        return Fragment()
