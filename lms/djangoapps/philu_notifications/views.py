from django.contrib.auth.decorators import login_required
from edx_notifications.lib.consumer import get_notifications_for_user
from edxmako.shortcuts import render_to_response


@login_required
def my_all_notifications(request):
    return render_to_response("philu_notifications/all_notifications.html")
