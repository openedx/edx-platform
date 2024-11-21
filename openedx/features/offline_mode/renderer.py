"""
This module contains the XBlockRenderer class,
which is responsible for rendering an XBlock HTML content from the LMS.
"""
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpRequest

from opaque_keys.edx.keys import UsageKey
from xmodule.modulestore.django import modulestore

from common.djangoapps.edxmako.shortcuts import render_to_string
from lms.djangoapps.courseware.block_render import get_block_by_usage_id
from lms.djangoapps.courseware.views.views import get_optimization_flags_for_content

from openedx.core.lib.courses import get_course_by_id
from openedx.features.course_experience.utils import dates_banner_should_display
from openedx.features.course_experience.url_helpers import get_learning_mfe_home_url

User = get_user_model()
log = logging.getLogger(__name__)


class XBlockRenderer:
    """
    Renders an XBlock HTML content from the LMS.
    Since imports from LMS are used here, XBlockRenderer can be called only in the LMS runtime.
    :param usage_key_string: The string representation of the block UsageKey.
    :param user: The user for whom the XBlock will be rendered.
    """

    SERVICE_USERNAME = 'offline_mode_worker'

    def __init__(self, usage_key_string, user=None, request=None):
        self.usage_key = UsageKey.from_string(usage_key_string)
        self.usage_key = self.usage_key.replace(course_key=modulestore().fill_in_run(self.usage_key.course_key))
        self.user = user or self.service_user
        self.request = request or self.generate_request()

    @property
    def service_user(self):
        """
        Returns a valid user to be used as the service user.
        """
        try:
            return User.objects.get(username=self.SERVICE_USERNAME)
        except User.DoesNotExist as e:
            log.error(f'Service user with username {self.SERVICE_USERNAME} to render XBlock does not exist.')
            raise e

    def generate_request(self):
        """
        Generates a request object with the service user and a session.
        """
        request = HttpRequest()
        request.user = self.user
        session = SessionStore()
        session.create()
        request.session = session
        return request

    def render_xblock_from_lms(self):
        """
        Returns a string representation of the HTML content of the XBlock as it appears in the LMS.
        Blocks renders without header, footer and navigation.
        Blocks view like a for regular user without staff or superuser access.
        """
        course_key = self.usage_key.course_key

        with modulestore().bulk_operations(course_key):
            course = get_course_by_id(course_key)
            block, _ = get_block_by_usage_id(
                self.request,
                str(course_key),
                str(self.usage_key),
                disable_staff_debug_info=True,
                course=course,
                will_recheck_access='1',
            )

            enable_completion_on_view_service = False
            wrap_xblock_data = None
            completion_service = block.runtime.service(block, 'completion')
            if completion_service and completion_service.completion_tracking_enabled():
                if completion_service.blocks_to_mark_complete_on_view({block}):
                    enable_completion_on_view_service = True
                    wrap_xblock_data = {
                        'mark-completed-on-view-after-delay': completion_service.get_complete_on_view_delay_ms()
                    }

            fragment = self.get_fragment(block, wrap_xblock_data)
            optimization_flags = get_optimization_flags_for_content(block, fragment)
            missed_deadlines, missed_gated_content = dates_banner_should_display(course_key, self.user)

            context = {
                'fragment': fragment,
                'course': course,
                'block': block,
                'enable_completion_on_view_service': enable_completion_on_view_service,
                'xqa_server': settings.FEATURES.get('XQA_SERVER', 'http://your_xqa_server.com'),
                'missed_deadlines': missed_deadlines,
                'missed_gated_content': missed_gated_content,
                'has_ended': course.has_ended(),
                'web_app_course_url': get_learning_mfe_home_url(course_key=course.id, url_fragment='home'),
                'disable_accordion': True,
                'allow_iframing': True,
                'disable_header': True,
                'disable_footer': True,
                'disable_window_wrap': True,
                'edx_notes_enabled': False,
                'staff_access': False,
                'on_courseware_page': True,
                'is_learning_mfe': False,
                'is_mobile_app': True,
                'is_offline_content': True,
                'render_course_wide_assets': True,
                'LANGUAGE_CODE': 'en',

                **optimization_flags,
            }
            return render_to_string('courseware/courseware-chromeless.html', context, namespace='main')

    @staticmethod
    def get_fragment(block, wrap_xblock_data=None):
        """
        Returns the HTML fragment of the XBlock.
        """
        student_view_context = {
            'show_bookmark_button': '0',
            'show_title': '1',
            'hide_access_error_blocks': True,
            'is_mobile_app': True,
        }
        if wrap_xblock_data:
            student_view_context['wrap_xblock_data'] = wrap_xblock_data
        return block.render('student_view', context=student_view_context)
