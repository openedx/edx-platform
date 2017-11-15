"""
Signle support contact view
"""
from django.conf import settings
from django.views.generic import View
from edxmako.shortcuts import render_to_response
from student.models import CourseEnrollment

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.features.enterprise_support import api as enterprise_api


class ContactUsView(View):
    """
    View for viewing and submitting contact us form.
    """

    def get(self, request):
        context = {
            'platform_name': configuration_helpers.get_value('platform_name', settings.PLATFORM_NAME),
            'zendesk_api_host': settings.ZENDESK_URL,
            'access_token': settings.ZENDESK_OAUTH_ACCESS_TOKEN,
            'custom_fields': settings.ZENDESK_CUSTOM_FIELDS
        }

        # Tag all issues with LMS to distinguish channel in Zendesk; requested by student support team
        zendesk_tags = ['LMS']

        # Per edX support, we would like to be able to route feedback items by site via tagging
        current_site_name = configuration_helpers.get_value("SITE_NAME")
        if current_site_name:
            current_site_name = current_site_name.replace(".", "_")
            zendesk_tags.append("site_name_{site}".format(site=current_site_name))

        if request.user.is_authenticated():
            context['user_enrollments'] = CourseEnrollment.enrollments_for_user(request.user)
            enterprise_learner_data = enterprise_api.get_enterprise_learner_data(site=request.site, user=request.user)
            if enterprise_learner_data:
                zendesk_tags.append('enterprise_learner')

        context['zendesk_tags'] = zendesk_tags

        return render_to_response("support/contact_us.html", context)
