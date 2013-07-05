from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotAllowed
from notification_prefs import NOTIFICATION_PREF_KEY
from user_api.models import UserPreference


def _validate(request):
    """
    Ensure that `request` is valid

    If the request is invalid, an appropriate response is returned. Otherwise,
    None is returned.
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    if not request.user.is_authenticated():
        return HttpResponseForbidden()


def enable(request):
    validation_response = _validate(request)
    if validation_response is not None:
        return validation_response

    UserPreference.objects.get_or_create(
        user=request.user,
        key=NOTIFICATION_PREF_KEY
    )

    return HttpResponse(status=204)


def disable(request):
    validation_response = _validate(request)
    if validation_response is not None:
        return validation_response

    UserPreference.objects.filter(
        user=request.user,
        key=NOTIFICATION_PREF_KEY
    ).delete()

    return HttpResponse(status=204)
