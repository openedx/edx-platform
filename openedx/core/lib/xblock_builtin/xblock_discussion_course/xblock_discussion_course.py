# -*- coding: utf-8 -*-
"""
Course Discussion XBlock
"""
import logging

from xblockutils.resources import ResourceLoader

from xblock.core import XBlock
from xblock.fields import Scope, String
from xblock.fragment import Fragment

from utils import _, add_resources_to_fragment, asset_to_static_url, render_mustache_templates


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

        fragment.add_css_url(asset_to_static_url('css/discussion/lms-discussion-main.css'))
        fragment.add_css_url(asset_to_static_url('xblock/discussion/css/discussion-course-custom.css'))

        discussion_service = self.xmodule_runtime.service(self, 'discussion')  # pylint: disable=no-member
        context = discussion_service.get_course_template_context()
        context['enable_new_post_btn'] = True

        add_resources_to_fragment(fragment)

        fragment.add_content(self.runtime.render_template('discussion/_discussion_course.html', context))

        fragment.add_javascript(loader.render_template('static/js/discussion_course.js', {
            'course_id': self.course_id
        }))

        fragment.add_content(render_mustache_templates())

        fragment.initialize_js('DiscussionCourseBlock')

        return fragment

    def _student_view_studio(self):
        """ Renders student view for Studio """
        fragment = Fragment()
        context = None
        fragment.add_content(self.runtime.render_template('discussion/_discussion_course_studio.html', context))
        fragment.add_css_url(asset_to_static_url('xblock/discussion/css/discussion-studio.css'))
        return fragment

    def studio_view(self, context=None):  # pylint: disable=unused-argument
        """ Renders author view Studio """
        return Fragment()
