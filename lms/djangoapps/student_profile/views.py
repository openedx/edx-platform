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

from django.utils.translation import ugettext as _


@login_required
@require_http_methods(['GET'])
def learner_profile(request, username):
    """Render the profile page for the specified username.

    Args:
        request (HttpRequest)
        username (str): username of user whose profile is requested.

    Returns:
        HttpResponse: 200 if the page was sent successfully
        HttpResponse: 302 if not logged in (redirect to login page)
        HttpResponse: 404 if the specified username does not exist
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
    """Context for the learner profile page.

    Args:
        logged_in_username (str): Username of user logged In user.
        profile_username (str): username of user whose profile is requested.
        user_is_staff (bool): Logged In user has staff access.

    Returns:
        dict

    Raises:
        ObjectDoesNotExist: the specified profile_username does not exist.
    """
    profile_user = User.objects.get(username=profile_username)

    country_options = [
        (country_code, _(country_name))  # pylint: disable=translation-of-non-string
        for country_code, country_name in sorted(
            countries.countries, key=lambda(__, name): unicode(name)
        )
    ]

    context = {
        'data': {
            'profile_user_id': profile_user.id,
            'default_public_account_fields': settings.ACCOUNT_VISIBILITY_CONFIGURATION['public_fields'],
            'default_visibility': settings.ACCOUNT_VISIBILITY_CONFIGURATION['default_visibility'],
            'accounts_api_url': reverse("accounts_api", kwargs={'username': profile_username}),
            'preferences_api_url': reverse('preferences_api', kwargs={'username': profile_username}),
            'profile_image_upload_url': reverse('profile_image_upload', kwargs={'username': profile_username}),
            'profile_image_remove_url': reverse('profile_image_remove', kwargs={'username': profile_username}),
            'profile_image_max_bytes': settings.PROFILE_IMAGE_MAX_BYTES,
            'profile_image_min_bytes': settings.PROFILE_IMAGE_MIN_BYTES,
            'account_settings_page_url': reverse('account_settings'),
            'has_preferences_access': (logged_in_username == profile_username or user_is_staff),
            'own_profile': (logged_in_username == profile_username),
            'country_options': country_options,
            'language_options': settings.ALL_LANGUAGES,
        }
    }

    return context
