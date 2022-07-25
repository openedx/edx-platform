"""
Views for the learner dashboard.
"""
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET

from common.djangoapps.edxmako.shortcuts import marketing_link
from common.djangoapps.util.json_request import JsonResponse
from lms.djangoapps.learner_dashboard.serializers import LearnerDashboardSerializer
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


def get_platform_settings():
    """Get settings used for platform level connections: emails, url routes, etc."""

    return {
        "supportEmail": settings.DEFAULT_FEEDBACK_EMAIL,
        "billingEmail": settings.PAYMENT_SUPPORT_EMAIL,
        "courseSearchUrl": marketing_link("COURSES"),
    }


def get_user_account_confirmation_info(user):
    """Determine if a user needs to verify their account and related URL info"""

    activation_email_support_link = (
        configuration_helpers.get_value(
            "ACTIVATION_EMAIL_SUPPORT_LINK", settings.ACTIVATION_EMAIL_SUPPORT_LINK
        )
        or settings.SUPPORT_SITE_LINK
    )

    email_confirmation = {
        "isNeeded": not user.is_active,
        "sendEmailUrl": activation_email_support_link,
    }

    return email_confirmation


@login_required
@require_GET
def dashboard_view(request):  # pylint: disable=unused-argument
    """List of courses a user is enrolled in or entitled to"""

    # Get user, determine if user needs to confirm email account
    user = request.user
    email_confirmation = get_user_account_confirmation_info(user)

    learner_dash_data = {
        "emailConfirmation": email_confirmation,
        "enterpriseDashboards": None,
        "platformSettings": get_platform_settings(),
        "enrollments": [],
        "unfulfilledEntitlements": [],
        "suggestedCourses": [],
    }

    response_data = LearnerDashboardSerializer(learner_dash_data).data
    return JsonResponse(response_data)
