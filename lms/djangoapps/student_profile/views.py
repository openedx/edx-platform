""" Views for a student's profile information. """

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django_countries import countries

from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods

from edxmako.shortcuts import render_to_response
from student.models import User


@login_required
@require_http_methods(['GET'])
def learner_profile(request, username):
    """
    Render the students profile page.

    Args:
        request (HttpRequest)
        username (str): username of user whose profile is requested.

    Returns:
        HttpResponse: 200 if the page was sent successfully
        HttpResponse: 302 if not logged in (redirect to login page)
        HttpResponse: 405 if using an unsupported HTTP method

    Example usage:
        GET /account/profile
    """
    try:
        return render_to_response(
            'student_profile/learner_profile.html',
            learner_profile_context(request.user.username, username, request.user.is_staff)
        )
    except ObjectDoesNotExist:
        return HttpResponse(status=404)


def learner_profile_context(logged_in_username, profile_username, user_is_staff):
    """
    Context for the learner profile page.

    Args:
        logged_in_username (str): Username of user logged In user.
        profile_username (str): username of user whose profile is requested.
        user_is_staff (bool): Logged In user has staff access.

    Returns:
        dict
    """
    profile_user = User.objects.get(username=profile_username)
    language_options = [language for language in settings.ALL_LANGUAGES]

    country_options = [
        (country_code, unicode(country_name))
        for country_code, country_name in sorted(
            countries.countries, key=lambda(__, name): unicode(name)
        )
    ]

    context = {
        'data': {
            'profile_user_id': profile_user.id,
            'default_public_account_fields': settings.ACCOUNT_VISIBILITY_CONFIGURATION['public_fields'],
            'accounts_api_url': reverse("accounts_api", kwargs={'username': profile_username}),
            'preferences_api_url': reverse('preferences_api', kwargs={'username': profile_username}),
            'account_settings_page_url': reverse('account_settings'),
            'has_preferences_access': (logged_in_username == profile_username or user_is_staff),
            'own_profile': (logged_in_username == profile_username),
            'country_options': country_options,
            'language_options': language_options,
        }
    }

    return context
