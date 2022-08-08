"""
Mock implementation of the Learner Home.
Returns statically authored JSON data
"""

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from common.djangoapps.util.json_request import JsonResponse


# Edit me to change response data
mock_data = {
    "foo": "bar",
}


@login_required
@require_GET
def dashboard_view(request):  # pylint: disable=unused-argument
    return JsonResponse(mock_data)
