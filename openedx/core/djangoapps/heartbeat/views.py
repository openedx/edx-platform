"""
Views for verifying the health (heartbeat) of the app.
"""
from util.json_request import JsonResponse

from .runchecks import runchecks


def heartbeat(request):
    """
    Simple view that a loadbalancer can check to verify that the app is up. Returns a json doc
    of service id: status or message. If the status for any service is anything other than True,
    it returns HTTP code 503 (Service Unavailable); otherwise, it returns 200.
    """
    check_results = {}
    try:
        check_results = runchecks('extended' in request.GET)

        status_code = 200  # Default to OK
        for check in check_results:
            if not check_results[check]['status']:
                status_code = 503  # 503 on any failure
    except Exception as e:
        status_code = 503
        check_results = {'error': unicode(e)}

    return JsonResponse(check_results, status=status_code)
