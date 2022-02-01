""" Views for a student's profile information. """


from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django_countries import countries

from lms.djangoapps.badges.utils import badges_enabled
from common.djangoapps.edxmako.shortcuts import marketing_link
from openedx.core.djangoapps.credentials.utils import get_credentials_records_url
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_api.accounts.api import get_account_settings
from openedx.core.djangoapps.user_api.errors import UserNotAuthorized, UserNotFound
from openedx.core.djangoapps.user_api.preferences.api import get_user_preferences
from openedx.features.learner_profile.toggles import should_redirect_to_profile_microfrontend
from openedx.features.learner_profile.views.learner_achievements import LearnerAchievementsFragmentView
from common.djangoapps.student.models import User


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
    if should_redirect_to_profile_microfrontend():
        profile_microfrontend_url = f"{settings.PROFILE_MICROFRONTEND_URL}{username}"
        if request.GET:
            profile_microfrontend_url += f'?{request.GET.urlencode()}'
        return redirect(profile_microfrontend_url)

    try:
        context = learner_profile_context(request, username, request.user.is_staff)
        return render(
            request=request,
            template_name='learner_profile/learner_profile.html',
            context=context
        )
    except (UserNotAuthorized, UserNotFound, ObjectDoesNotExist):
        raise Http404  # lint-amnesty, pylint: disable=raise-missing-from


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
        'own_profile': own_profile,
        'platform_name': configuration_helpers.get_value('platform_name', settings.PLATFORM_NAME),
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
            'social_platforms': settings.SOCIAL_PLATFORMS,
            'enable_coppa_compliance': settings.ENABLE_COPPA_COMPLIANCE,
            'parental_consent_age_limit': settings.PARENTAL_CONSENT_AGE_LIMIT
        },
        'show_program_listing': ProgramsApiConfig.is_enabled(),
        'show_dashboard_tabs': True,
        'disable_courseware_js': True,
        'nav_hidden': True,
        'records_url': get_credentials_records_url(),
    }

    if own_profile or user_is_staff:
        achievements_fragment = LearnerAchievementsFragmentView().render_to_fragment(
            request,
            username=profile_user.username,
            own_profile=own_profile,
        )
        context['achievements_fragment'] = achievements_fragment

    if badges_enabled():
        context['data']['badges_api_url'] = reverse("badges_api:user_assertions", kwargs={'username': profile_username})

    return context
