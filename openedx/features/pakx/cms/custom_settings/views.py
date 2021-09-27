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
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.features.pakx.lms.overrides.utils import get_or_create_course_overview_content
from util.views import ensure_valid_course_key

from .models import CourseOverviewContent, CourseSet

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
        course_sets = CourseSet.objects.filter(
            publisher_org__organizationcourse__course_id=course_key, is_active=True
        ).only(
            'id', 'name'
        )

        course_overview_url = u'{overview_base_url}/courses/{course_key}/overview'.format(
            overview_base_url=configuration_helpers.get_value('LMS_ROOT_URL', settings.LMS_ROOT_URL),
            course_key=course_key,
        )
        course_overview_content = get_or_create_course_overview_content(course_key)
        context = {
            'course_sets': course_sets,
            'context_course': context_course,
            'overview_content': course_overview_content,
            'course_overview_url': course_overview_url,
            'custom_settings_url': reverse('custom_settings', kwargs={'course_key_string': course_key})
        }
        return render(request, self.template_name, context=context)

    def post(self, request, course_key_string):
        """
        Save course overview content in model and display updated version of custom settings page
        """
        course_key = CourseKey.from_string(course_key_string)

        course_set = request.POST['course-set']
        course_overview = request.POST['course-overview']
        card_description = request.POST['card-description']
        publisher_logo_url = request.POST['publisher-logo-url']
        course_experience = request.POST.get('course_experience', 0)

        if course_overview is not None:
            CourseOverviewContent.objects.update_or_create(
                course_id=course_key,
                defaults={
                    'course_set_id': course_set,
                    'body_html': course_overview,
                    'card_description': card_description,
                    'course_experience': course_experience,
                    'publisher_logo_url': publisher_logo_url,
                }
            )

        return redirect(reverse('custom_settings', kwargs={'course_key_string': course_key}))
