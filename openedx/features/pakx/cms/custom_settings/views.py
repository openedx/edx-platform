"""
All views for custom settings app
"""
import logging

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import View
from opaque_keys.edx.keys import CourseKey

from cms.djangoapps.contentstore.views.course import get_course_and_check_access
from edxmako.shortcuts import render_to_string
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from util.views import ensure_valid_course_key

from .models import CourseOverviewContent

log = logging.getLogger(__name__)


@method_decorator(ensure_csrf_cookie, name='dispatch')
@method_decorator(ensure_valid_course_key, name='dispatch')
class CourseCustomSettingsView(LoginRequiredMixin, View):
    """
    A view for PakistanX specific custom settings for a course
    """
    template_name = 'custom_settings.html'

    def get(self, request, course_key_string):
        """
        Show course custom settings page with course overview content editor
        """
        course_key = CourseKey.from_string(course_key_string)
        context_course = get_course_and_check_access(course_key, request.user)

        course_overview_url = u'{overview_base_url}/courses/{course_key}/overview'.format(
            overview_base_url=configuration_helpers.get_value('LMS_ROOT_URL', settings.LMS_ROOT_URL),
            course_key=course_key,
        )
        default_content = render_to_string('courseware/overview.html', {})
        course_overview_content, _ = CourseOverviewContent.objects.get_or_create(
            course_id=course_key,
            defaults={'body_html': default_content}
        )
        context = {
            'context_course': context_course,
            'default_content': course_overview_content.body_html,
            'course_overview_url': course_overview_url,
            'custom_settings_url': reverse('custom_settings', kwargs={'course_key_string': course_key})
        }
        return render(request, self.template_name, context=context)

    def post(self, request, course_key_string):
        """
        Save course overview content in model and display updated version of custom settings page
        """
        course_key = CourseKey.from_string(course_key_string)
        course_overview = request.POST['course-overview']
        if course_overview is not None:
            CourseOverviewContent.objects.update_or_create(
                course_id=course_key, defaults={'body_html': course_overview}
            )

        return redirect(reverse('custom_settings', kwargs={'course_key_string': course_key}))
