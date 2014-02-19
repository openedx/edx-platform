"""
Views for accessing language preferences
"""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest

from user_api.models import UserPreference
from lang_pref import LANGUAGE_KEY


@login_required
def set_language(request):
    """
    This view is called when the user would like to set a language preference
    """
    user = request.user
    lang_pref = request.POST.get('language', None)

    if lang_pref:
        UserPreference.set_preference(user, LANGUAGE_KEY, lang_pref)
        return HttpResponse('{"success": true}')

    return HttpResponseBadRequest('no language provided')
