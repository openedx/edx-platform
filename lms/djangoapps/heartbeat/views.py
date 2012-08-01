import json
from datetime import datetime
from django.http import HttpResponse


def heartbeat(request):
    """
    Simple view that a loadbalancer can check to verify that the app is up
    """
    output = {
        'date': datetime.now().isoformat()
    }
    return HttpResponse(json.dumps(output, indent=4))
