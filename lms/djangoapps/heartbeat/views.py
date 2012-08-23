import json
from datetime import datetime
from django.http import HttpResponse
from xmodule.modulestore.django import modulestore


def heartbeat(request):
    """
    Simple view that a loadbalancer can check to verify that the app is up
    """
    output = {
        'date': datetime.now().isoformat(),
        'courses': [course.location.url() for course in modulestore().get_courses()],
    }
    return HttpResponse(json.dumps(output, indent=4))
