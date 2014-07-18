from xmodule.modulestore.django import modulestore
from dogapi import dog_stats_api
from util.json_request import JsonResponse
from django.db import connection
from django.db.utils import DatabaseError
from xmodule.exceptions import HeartbeatFailure


@dog_stats_api.timed('edxapp.heartbeat')
def heartbeat(request):
    """
    Simple view that a loadbalancer can check to verify that the app is up. Returns a json doc
    of service id: status or message. If the status for any service is anything other than True,
    it returns HTTP code 503 (Service Unavailable); otherwise, it returns 200.
    """
    # This refactoring merely delegates to the default modulestore (which if it's mixed modulestore will
    # delegate to all configured modulestores) and a quick test of sql. A later refactoring may allow
    # any service to register itself as participating in the heartbeat. It's important that all implementation
    # do as little as possible but give a sound determination that they are ready.
    try:
        output = modulestore().heartbeat()
    except HeartbeatFailure as fail:
        return JsonResponse({fail.service: unicode(fail)}, status=503)

    cursor = connection.cursor()
    try:
        cursor.execute("SELECT CURRENT_DATE")
        cursor.fetchone()
        output['SQL'] = True
    except DatabaseError as fail:
        return JsonResponse({'SQL': unicode(fail)}, status=503)

    return JsonResponse(output)
