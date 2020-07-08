import json
from copy import deepcopy
from datetime import datetime
from logging import getLogger

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models.signals import post_save
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import get_language
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods
from pytz import UTC

import analytics
from edxmako.shortcuts import render_to_response
from eventtracking import tracker
from lms.djangoapps.onboarding.models import EmailPreference, Organization, PartnerNetwork, UserExtendedProfile
from nodebb.helpers import set_user_activation_status_on_nodebb, update_nodebb_for_user_status
from notification_prefs.views import enable_notifications
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.user_api.preferences import api as preferences_api
from openedx.core.djangoapps.user_api.views import RegistrationView
from openedx.core.djangoapps.user_authn.cookies import set_logged_in_cookies
from openedx.core.djangoapps.user_authn.views.register import REGISTER_USER, record_registration_attributions
from openedx.features.partners.helpers import auto_join_partner_community, get_partner_recommended_courses
from openedx.features.partners.models import PartnerUser
from openedx.features.student_account.helpers import save_user_utm_info, get_registration_countries
from philu_overrides.user_api.views import LoginSessionViewCustom
from rest_framework import status
from student.models import Registration, UserProfile
from student.views import password_change_request_handler

from . import constants as partner_constants
from .forms import PartnerAccountCreationForm, PartnerResetPasswordForm
from .helpers import import_form_using_slug, user_has_performance_access
from .models import Partner

log = getLogger(__name__)
AUDIT_LOG = getLogger('audit')


def dashboard(request, slug):
    partner = get_object_or_404(Partner, slug=slug)
    courses = get_partner_recommended_courses(partner.slug, request.user)
    registration_countries = get_registration_countries()

    context = {
        'recommended_courses': courses,
        'slug': partner.slug, 'partner': partner,
        'registration_countries': registration_countries,
    }

    return render_to_response('features/partners/dashboard.html', context)


def performance_dashboard(request, slug):
    partner = get_object_or_404(Partner, slug=slug)
    if user_has_performance_access(request.user, partner):
        return render_to_response('features/partners/performance_dashboard.html',
                                  {'slug': partner.slug, 'partner': partner,
                                   'performance_url': partner.performance_url})
    return HttpResponseForbidden()


class PartnerLimitReachedError(Exception):
    pass


@require_http_methods(['POST'])
@sensitive_post_parameters('password')
def register_user(request, slug):
    """
    This is general registering view, for users of all partners
    :param request: The HttpRequest request object.
    :param slug: partner slug
    :return: JsonResponse object with success/error message
    """
    partner = get_object_or_404(Partner, slug=slug)
    return PartnerRegistrationView.as_view()(request, partner=partner)


@require_http_methods(['POST'])
@sensitive_post_parameters('password')
def login_user(request, slug):
    """
    This is general login view, for users of all partners
    :param request: The HttpRequest request object.
    :param slug: partner slug
    :return: JsonResponse object with success/error message
    """
    partner = get_object_or_404(Partner, slug=slug)
    return PartnerLoginSessionView.as_view()(request, partner=partner)


@require_http_methods(['POST'])
def reset_password_view(request):
    """
    This is the basic password reset view, as per the requirements
    of organization password reset flow. Have to send 404 if user does
    not exist
    :param request: The HttpRequest request object.
    :return: HTTPResponse/JSONResponse object with success/error status code
    """
    email = request.POST.get('email')
    reset_password_form = PartnerResetPasswordForm(data={'email': email})
    if reset_password_form.is_valid():
        response = password_change_request_handler(request)
        if response.status_code == status.HTTP_403_FORBIDDEN:
            return JsonResponse({'Error': {'email': [response.content]}}, status=status.HTTP_403_FORBIDDEN)
        return response
    return JsonResponse({'Error': dict(reset_password_form.errors.items())}, status=status.HTTP_404_NOT_FOUND)


class PartnerRegistrationView(RegistrationView):
    """
    This class handles registration flow for partner users. It inherit some basic functionality from original (normal)
    registration flow
    """

    def get(self, request, partner):
        # Overriding get method to suppress corresponding method of parent class
        raise Http404

    def post(self, request, partner):
        registration_data = request.POST.copy()

        # validate data provided by end user
        # PhilU implementation to import custom form if it exists
        # Note that the override form must be named `AccountCreationFormCustom`
        form = import_form_using_slug(partner.slug)
        account_creation_form = form.AccountCreationFormCustom(data=registration_data, tos_required=True) if form \
            else PartnerAccountCreationForm(data=registration_data, tos_required=True)
        if not account_creation_form.is_valid():
            return JsonResponse({'Error': dict(account_creation_form.errors.items())}, status=400)

        account_creation_form.clean_registration_data(registration_data)
        try:
            # Create or update models for User, UserProfile,
            # UserExtendedProfile, Organization, PartnerUser and EmailPreference
            user = create_account_with_params_custom(request, registration_data, partner)
            save_user_utm_info(request, user)
        except PartnerLimitReachedError as er:
            error_message = {'Error': er.message,
                             'Partner': partner.label}
            log.exception(error_message)
            return JsonResponse(error_message, status=400)
        except Exception as err:
            error_message = {'Error': {'reason': 'User registration failed due to {}'.format(repr(err))}}
            log.exception(error_message)
            return JsonResponse(error_message, status=400)

        response = JsonResponse({'success': True})
        set_logged_in_cookies(request, response, user)
        return response


def create_account_with_params_custom(request, params, partner):
    # Copy params so we can modify it; we can't just do dict(params) because if
    # params is request.POST, that results in a dict containing lists of values
    params = dict(params.items())

    first_name, last_name = params['name']
    # Perform operations within a transaction that are critical to account creation
    with transaction.atomic():
        try:
            # Create user and activate it
            user = User(
                username=params['username'],
                email=params['email'],
                first_name=first_name,
                last_name=last_name,
                is_active=True,
            )
            user.set_password(params['password'])
            registration = Registration()

            user.save()
            registration.register(user)
        except Exception as err:  # pylint: disable=broad-except
            log.exception('User creation failed for user {username}'.format(username=params['username']), repr(err))
            raise

        extended_profile_data = deepcopy(partner_constants.PARTNER_EXTENDED_PROFILE_DEFAULT_DATA)
        extended_profile_data[partner_constants.START_MONTH_YEAR_KEY] = datetime.now().strftime('%m/%Y')

        user_profile_data = deepcopy(partner_constants.PARTNER_USER_PROFILE_DEFAULT_DATA)
        user_profile_data['name'] = user.get_full_name()
        user_profile_data['country'] = params['country']

        try:
            # Create user profile
            profile = UserProfile(user=user, **user_profile_data)
            profile.meta = json.dumps(extended_profile_data)
            profile.save()

            # We have to manually trigger the post_save so that profile is synced on nodebb
            post_save.send(UserProfile, instance=profile, created=False)

        except Exception as err:  # pylint: disable=broad-except
            log.exception('UserProfile creation failed for user {id}.'.format(id=user.id), repr(err))
            raise

        try:
            organization_data = deepcopy(partner_constants.PARTNER_ORGANIZATION_DEFAULT_DATA)
            organization_data[partner_constants.ORG_TYPE_KEY] = PartnerNetwork.NON_PROFIT_ORG_TYPE_CODE

            organization_name = params['organization_name']
            organization_to_assign = Organization.objects.filter(label__iexact=organization_name).first()

            if not organization_to_assign:
                # Create organization if not already exists
                organization_to_assign = Organization.objects.create(label=organization_name, **organization_data)
                organization_to_assign.save()

            # Make user first learner either if his organization is new or his organization is orphan
            extended_profile_data[
                partner_constants.IS_FIRST_LEARNER] = organization_to_assign.can_join_as_first_learner(
                exclude_user=user)

            if extended_profile_data[partner_constants.IS_FIRST_LEARNER]:
                # submit organization detail form
                extended_profile_data[partner_constants.IS_ORGANIZATION_METRICS_SUBMITTED] = True

            # create User Extended Profile
            extended_profile = UserExtendedProfile.objects.create(
                user=user, organization=organization_to_assign, **extended_profile_data
            )

            extended_profile.save()
        except Exception as err:  # pylint: disable=broad-except
            log.exception('User extended profile creation failed for user {id}.'.format(id=user.id), repr(err))
            raise

        try:
            # create a bridge between user and partner
            partner_user = PartnerUser.objects.create(user=user, partner=partner)
            partner_user.save()
        except Exception as err:  # pylint: disable=broad-except
            log.exception('partner_user creation failed for user {id}, partner {slug}'
                          .format(id=user.id, slug=partner.slug), repr(err))
            raise

        try:
            user_email_preferences, created = EmailPreference.objects.get_or_create(user=user)
            user_email_preferences.opt_in = partner_constants.OPT_IN_DATA
            user_email_preferences.save()
        except Exception as err:  # pylint: disable=broad-except
            log.exception('User email preferences creation failed for user {id}.'.format(id=user.id), repr(err))
            raise

    # Perform operations that are non-critical parts of account creation
    preferences_api.set_user_preference(user, LANGUAGE_KEY, get_language())

    auto_join_partner_community(partner, user)

    if settings.FEATURES.get('ENABLE_DISCUSSION_EMAIL_DIGEST'):
        try:
            enable_notifications(user)
        except Exception:  # pylint: disable=broad-except
            log.exception('Enable discussion notifications failed for user {id}.'.format(id=user.id))

    # Track the user's registration
    if hasattr(settings, 'LMS_SEGMENT_KEY') and settings.LMS_SEGMENT_KEY:
        tracking_context = tracker.get_tracker().resolve_context()
        identity_args = [
            user.id,  # pylint: disable=no-member
            {
                'email': user.email,
                'username': user.username,
                'name': profile.name,
                # Mailchimp requires the age & yearOfBirth to be integers, we send a sane integer default if falsey.
                'age': profile.age or -1,
                'yearOfBirth': profile.year_of_birth or datetime.now(UTC).year,
                'education': profile.level_of_education_display,
                'address': profile.mailing_address,
                'gender': profile.gender_display,
                'country': unicode(profile.country),
            }
        ]

        if hasattr(settings, 'MAILCHIMP_NEW_USER_LIST_ID'):
            identity_args.append({
                'MailChimp': {
                    'listId': settings.MAILCHIMP_NEW_USER_LIST_ID
                }
            })

        analytics.identify(*identity_args)

        analytics.track(
            user.id,
            'edx.bi.user.account.registered',
            {
                'category': 'conversion',
                'label': params.get('course_id'),
                'provider': None
            },
            context={
                'ip': tracking_context.get('ip'),
                'Google Analytics': {
                    'clientId': tracking_context.get('client_id')
                }
            }
        )

    # Activate user on nodebb manually
    set_user_activation_status_on_nodebb(params['username'], True)

    # Since all required data corresponding to new user is saved in relevant models
    # request NodeBB to register user
    update_nodebb_for_user_status(params['username'])

    # Announce registration
    REGISTER_USER.send(sender=None, user=user, registration=registration)
    if not registration.user.is_active:
        registration.activate()

    count_registered_partner_users = PartnerUser.objects.filter(partner=partner).count()
    limit_registered_partner_users = partner.configuration.get('USER_LIMIT')

    if limit_registered_partner_users and count_registered_partner_users > int(limit_registered_partner_users):
        partner_user.status = partner_constants.PARTNER_USER_STATUS_WAITING
        partner_user.save()
        raise PartnerLimitReachedError('Partner registration limit reached for partner {}'.format(partner.label))
    else:
        # login user immediately after a user creates an account,
        new_user = authenticate(username=user.username, password=params['password'])
        login(request, new_user)
        request.session.set_expiry(0)

    try:
        record_registration_attributions(request, new_user)
    # Don't prevent a user from registering due to attribution errors.
    except Exception:  # pylint: disable=broad-except
        log.exception('Error while attributing cookies to user registration.')

    # TODO: there is no error checking here to see that the user actually logged in successfully,
    # and is not yet an active user.
    if new_user is not None:
        AUDIT_LOG.info(u'Login success on new account creation - {0}'.format(new_user.username))

    return new_user


class PartnerLoginSessionView(LoginSessionViewCustom):
    """
    Inherited from LoginSessionViewCustom to keep the existing flow for login
    and extend the functionality to affiliate the user with Partner if not already done
    """

    def post(self, request, partner):

        response = super(PartnerLoginSessionView, self).post(request)

        if response.status_code == status.HTTP_200_OK:
            user = request.user
            try:
                PartnerUser.objects.get_or_create(partner=partner, user=user)
            except Exception as ex:
                log.error('Failed to affiliate {user} with {partner} due to exception {exp}'.format(
                    user=user.username, partner=partner.slug, exp=str(ex))
                )
        return response
