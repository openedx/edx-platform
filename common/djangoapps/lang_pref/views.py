"""
Views for accessing language preferences
"""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest

from openedx.core.djangoapps.user_api.preferences.api import set_user_preference
from lang_pref import LANGUAGE_KEY


@login_required
def set_language(request):
    """
    This view is called when the user would like to set a language preference
    """
    lang_pref = request.POST.get('language', None)

    if lang_pref:
        set_user_preference(request.user, LANGUAGE_KEY, lang_pref)
        return HttpResponse('{"success": true}')

    return HttpResponseBadRequest('no language provided')
