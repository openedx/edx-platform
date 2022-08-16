"""
Mock implementation of the Learner Home.
Returns statically authored JSON data
"""
# pylint: disable=line-too-long

import json
from os import path

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from common.djangoapps.util.json_request import JsonResponse

LEARNER_HOME_DIR = "/edx/app/edxapp/edx-platform/lms/djangoapps/learner_home"
MOCK_DATA_FILE = "mock_data.json"


@login_required
@require_GET
def dashboard_view(request):  # pylint: disable=unused-argument

    with open(path.join(LEARNER_HOME_DIR, MOCK_DATA_FILE), "r") as mock_data_file:

        # Edit me to change response data
        mock_data = json.load(mock_data_file)

    return JsonResponse(mock_data)
