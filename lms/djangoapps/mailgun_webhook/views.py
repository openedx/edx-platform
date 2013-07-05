from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.http import HttpResponseNotFound
import hashlib
import hmac
from notification_prefs import NOTIFICATION_PREF_KEY
from user_api.models import UserPreference


def unsubscribe(request):
    """
    Process an unsubscribe request from Mailgun

    This updates a user's notification preference to match the unsubscription.

    Responses are empty because Mailgun does not process the response body.
    See http://documentation.mailgun.com/user_manual.html#manual-webhooks for
    more about Mailgun's webhooks. 
    """
    mailgun_key = getattr(settings, "MAILGUN_API_KEY", None)
    if mailgun_key is None:
        return HttpResponseNotFound()

    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    timestamp = request.POST.get("timestamp")
    token = request.POST.get("token")
    signature = request.POST.get("signature")
    event = request.POST.get("event")
    recipient = request.POST.get("recipient")
    if (
        timestamp is None or
        token is None or
        signature is None or
        event is None or
        recipient is None
    ):
        return HttpResponseBadRequest()

    computed_signature = hmac.new(
        key=mailgun_key,
        msg="{timestamp}{token}".format(timestamp=timestamp, token=token),
        digestmod=hashlib.sha256
    ).hexdigest()
    if computed_signature != signature:
        return HttpResponseBadRequest()

    if event != "unsubscribed":
        return HttpResponseBadRequest()

    try:
        user = User.objects.get(email=recipient)
        UserPreference.objects.filter(user=user, key=NOTIFICATION_PREF_KEY).delete()
    except User.DoesNotExist:
        # User has changed email address; we have no way to know who this is
        pass

    return HttpResponse()
