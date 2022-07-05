"""
Views for the learner dashboard.
"""
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET

from common.djangoapps.edxmako.shortcuts import marketing_link
from common.djangoapps.util.json_request import JsonResponse
from lms.djangoapps.learner_dashboard.serializers import LearnerDashboardSerializer


def get_platform_settings():
    """Get settings used for platform level connections: emails, url routes, etc."""

    return {
        "supportEmail": settings.DEFAULT_FEEDBACK_EMAIL,
        "billingEmail": settings.PAYMENT_SUPPORT_EMAIL,
        "courseSearchUrl": marketing_link("COURSES"),
    }


@login_required
@require_GET
def dashboard_view(request):  # pylint: disable=unused-argument
    """List of courses a user is enrolled in or entitled to"""
    learner_dash_data = {
        "platformSettings": get_platform_settings(),
        "enrollments": [],
        "unfulfilledEntitlements": [],
        "suggestedCourses": [],
    }

    response_data = LearnerDashboardSerializer(learner_dash_data).data
    return JsonResponse(response_data)
