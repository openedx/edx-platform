from django.conf import settings

from lms.djangoapps.philu_overrides.constants import ACTIVATION_ERROR, ACTIVATION_ALERT_TYPE


def get_global_alert_messages(request):

    """
    function to get application wide messages
    :param request:
    :return: returns list of global messages"
    """

    alert_messages = []
    if not request.is_ajax():
        if request.user.is_authenticated() and not request.user.is_active and '/activate/' not in request.path:
            alert_messages.append({
                "type": ACTIVATION_ALERT_TYPE,
                "alert": ACTIVATION_ERROR
            })
    return {"alert_messages": alert_messages}


def add_nodebb_endpoint(request):
    """
    Add our NODEBB_ENDPOINT to the template context so that it can be referenced by any client side code.
    """
    return { "nodebb_endpoint": settings.NODEBB_ENDPOINT }
