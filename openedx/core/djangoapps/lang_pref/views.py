"""
Language Preference Views
"""

import json

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.translation import LANGUAGE_SESSION_KEY

from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY


@ensure_csrf_cookie
def update_session_language(request):
    """
    Update the language session key.
    """
    if request.method == 'PATCH':
        data = json.loads(request.body)
        language = data.get(LANGUAGE_KEY, settings.LANGUAGE_CODE)
        if request.session.get(LANGUAGE_SESSION_KEY, None) != language:
            request.session[LANGUAGE_SESSION_KEY] = unicode(language)
    return HttpResponse(200)
