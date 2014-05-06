import json
from datetime import datetime
from pytz import UTC
from django.http import HttpResponse
from xmodule.modulestore.django import modulestore
from dogapi import dog_stats_api


@dog_stats_api.timed('edxapp.heartbeat')
def heartbeat(request):
    """
    Simple view that a loadbalancer can check to verify that the app is up
    """
    output = {
        'date': datetime.now(UTC).isoformat(),
        'courses': [course.location.to_deprecated_string() for course in modulestore().get_courses()],
    }
    return HttpResponse(json.dumps(output, indent=4))
