"""
Language Preference Views
"""


import json

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie

from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.lang_pref.helpers import get_language_cookie, set_language_cookie


@ensure_csrf_cookie
def update_language(request):
    """
    Update the language cookie.
    """
    response = HttpResponse(200)
    if request.method == 'PATCH':
        data = json.loads(request.body.decode('utf8'))
        language = data.get(LANGUAGE_KEY, settings.LANGUAGE_CODE)
        if get_language_cookie(request) != language:
            set_language_cookie(request, response, language)
    return response
