""" Views for a student's profile information. """

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import Http404
from django.views.decorators.http import require_http_methods
from django_countries import countries
from django.contrib.staticfiles.storage import staticfiles_storage

from badges.utils import badges_enabled
from edxmako.shortcuts import render_to_response, marketing_link
from openedx.core.djangoapps.user_api.accounts.api import get_account_settings
from openedx.core.djangoapps.user_api.errors import UserNotFound, UserNotAuthorized
from openedx.core.djangoapps.user_api.preferences.api import get_user_preferences
from student.models import User
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


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
        HttpResponse: 405 if using an unsupported HTTP method
    Raises:
        Http404: 404 if the specified user is not authorized or does not exist

    Example usage:
        GET /account/profile
    """
    try:
        return render_to_response(
            'student_profile/learner_profile.html',
            learner_profile_context(request, username, request.user.is_staff)
        )
    except (UserNotAuthorized, UserNotFound, ObjectDoesNotExist):
        raise Http404


def learner_profile_context(request, profile_username, user_is_staff):
    """Context for the learner profile page.

    Args:
        logged_in_user (object): Logged In user.
        profile_username (str): username of user whose profile is requested.
        user_is_staff (bool): Logged In user has staff access.
        build_absolute_uri_func ():

    Returns:
        dict

    Raises:
        ObjectDoesNotExist: the specified profile_username does not exist.
    """
    profile_user = User.objects.get(username=profile_username)
    logged_in_user = request.user

    own_profile = (logged_in_user.username == profile_username)

    account_settings_data = get_account_settings(request, [profile_username])[0]

    preferences_data = get_user_preferences(profile_user, profile_username)

    context = {
        'data': {
            'profile_user_id': profile_user.id,
            'default_public_account_fields': settings.ACCOUNT_VISIBILITY_CONFIGURATION['public_fields'],
            'default_visibility': settings.ACCOUNT_VISIBILITY_CONFIGURATION['default_visibility'],
            'accounts_api_url': reverse("accounts_api", kwargs={'username': profile_username}),
            'preferences_api_url': reverse('preferences_api', kwargs={'username': profile_username}),
            'preferences_data': preferences_data,
            'account_settings_data': account_settings_data,
            'profile_image_upload_url': reverse('profile_image_upload', kwargs={'username': profile_username}),
            'profile_image_remove_url': reverse('profile_image_remove', kwargs={'username': profile_username}),
            'profile_image_max_bytes': settings.PROFILE_IMAGE_MAX_BYTES,
            'profile_image_min_bytes': settings.PROFILE_IMAGE_MIN_BYTES,
            'account_settings_page_url': reverse('account_settings'),
            'has_preferences_access': (logged_in_user.username == profile_username or user_is_staff),
            'own_profile': own_profile,
            'country_options': list(countries),
            'find_courses_url': marketing_link('COURSES'),
            'language_options': settings.ALL_LANGUAGES,
            'badges_logo': staticfiles_storage.url('certificates/images/backpack-logo.png'),
            'badges_icon': staticfiles_storage.url('certificates/images/ico-mozillaopenbadges.png'),
            'backpack_ui_img': staticfiles_storage.url('certificates/images/backpack-ui.png'),
            'platform_name': configuration_helpers.get_value('platform_name', settings.PLATFORM_NAME),
        },
        'disable_courseware_js': True,
    }

    if badges_enabled():
        context['data']['badges_api_url'] = reverse("badges_api:user_assertions", kwargs={'username': profile_username})

    return context
