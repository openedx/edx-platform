"""
Views for the learner dashboard.
"""
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET

from common.djangoapps.util.json_request import JsonResponse
from lms.djangoapps.learner_dashboard.learner_apis import get_platform_settings
from lms.djangoapps.learner_dashboard.serializers import LearnerDashboardSerializer


@login_required
@require_GET
def dashboard_view(request):  # pylint: disable=unused-argument
    """List of courses a user is enrolled in or entitled to"""
    learner_dash_data = {
        "edx": get_platform_settings(),
        "enrollments": [],
        "unfulfilledEntitlements": [],
        "suggestedCourses": [],
    }

    response_data = LearnerDashboardSerializer(learner_dash_data).data
    return JsonResponse(response_data)
