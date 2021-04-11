"""
Language Preference Views
"""


import json

import six

from django.conf import settings
from django.http import HttpResponse
from django.utils.translation import LANGUAGE_SESSION_KEY
from django.views.decorators.csrf import ensure_csrf_cookie

from openedx.core.djangoapps.lang_pref import COOKIE_DURATION, LANGUAGE_KEY
from openedx.core.lib.mobile_utils import is_request_from_mobile_app


@ensure_csrf_cookie
def update_session_language(request):
    """
    Update the language session key.
    """
    response = HttpResponse(200)
    if request.method == 'PATCH':
        data = json.loads(request.body.decode('utf8'))
        language = data.get(LANGUAGE_KEY, settings.LANGUAGE_CODE)
        if request.session.get(LANGUAGE_SESSION_KEY, None) != language:
            request.session[LANGUAGE_SESSION_KEY] = six.text_type(language)
        response.set_cookie(
            settings.LANGUAGE_COOKIE,
            language,
            domain=settings.SESSION_COOKIE_DOMAIN,
            max_age=COOKIE_DURATION,
            secure=request.is_secure(),
        )
    return response
