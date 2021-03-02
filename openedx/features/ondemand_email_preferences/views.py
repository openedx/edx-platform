"""
Views for on-demand-email-preferences app.
"""
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from opaque_keys.edx.keys import CourseKey
from rest_framework import status

from lms.djangoapps.onboarding.helpers import get_email_pref_on_demand_course

log = logging.getLogger("edx.ondemand_email_preferences")


@login_required
def update_on_demand_emails_preferences_component(request, course_id, *args, **kwargs):  # pylint: disable=unused-argument

    """
    Used to fetch the email preferences of self paced course
    :param request:
    :course_id: Course id of Self paced Course
    :return:
    {
        "status": "200",
        "email_preferences": "boolean"
    }
    """

    email_preferences = get_email_pref_on_demand_course(request.user, CourseKey.from_string(course_id))
    return JsonResponse({'status': status.HTTP_200_OK, 'email_preferences': email_preferences})
