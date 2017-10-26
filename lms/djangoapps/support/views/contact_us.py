"""
Signle support contact view
"""
from django.conf import settings
from django.views.generic import View
from edxmako.shortcuts import render_to_response
from student.models import CourseEnrollment

from openedx.core.djangoapps.site_configuration import helpers


class ContactUsView(View):
    """
    View for viewing and submitting contact us form.
    """

    def get(self, request):
        context = {
            'platform_name': helpers.get_value('platform_name', settings.PLATFORM_NAME)
        }
        if request.user.is_authenticated():
            context['user_enrollments'] = CourseEnrollment.enrollments_for_user(request.user)

        return render_to_response("support/contact_us.html", context)
