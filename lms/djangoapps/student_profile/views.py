""" Views for a student's account information. """

import logging

from django.conf import settings
from django_countries import countries

from django.core.urlresolvers import reverse, resolve
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from dark_lang.models import DarkLangConfig
from edxmako.shortcuts import render_to_response, render_to_string

from student.models import UserProfile
import openedx.core.djangoapps.user_api.preferences.api as perf_api
import openedx.core.djangoapps.user_api.preferences.api as account_api



@login_required
@require_http_methods(['GET'])
def learner_profile(request, username):
    """Render the students profile page.
    Args:
        request (HttpRequest)
    Returns:
        HttpResponse: 200 if the page was sent successfully
        HttpResponse: 302 if not logged in (redirect to login page)
        HttpResponse: 405 if using an unsupported HTTP method
    Example usage:
        GET /account/profile
    """

    language_options = [language for language in settings.ALL_LANGUAGES]

    country_options = [
        (country_code, unicode(country_name))
        for country_code, country_name in sorted(
            countries.countries, key=lambda(__, name): unicode(name)
        )
    ]

    context = {
        'data': {
            'default_public_account_fields': settings.ACCOUNT_VISIBILITY_CONFIGURATION['public_fields'],
            'accounts_api_url': reverse("accounts_api", kwargs={'username': username}),
            'preferences_api_url': reverse('preferences_api', kwargs={'username': username}),
            'account_settings_page_url': reverse('account_settings'),
            'has_preferences_access': (request.user.username == username or request.user.is_staff),
            'own_profile': (request.user.username == username),
            'country_options': country_options,
            'language_options': language_options,
        }
    }
    return render_to_response('student_profile/learner_profile.html', context)