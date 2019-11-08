import analytics
import datetime
import json
import logging
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.validators import ValidationError
from django.db import transaction
from django.utils.translation import get_language
from edxmako.shortcuts import render_to_response
from eventtracking import tracker
from lms.djangoapps.onboarding.models import (
    EmailPreference,
    Organization,
    UserExtendedProfile
)
from lms.djangoapps.onboarding.models import RegistrationType
from lms.djangoapps.philu_overrides.helpers import save_user_partner_network_consent
from lms.djangoapps.philu_overrides.user_api.views import RegistrationViewCustom
from notification_prefs.views import enable_notifications
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_api.preferences import api as preferences_api
from openedx.core.djangoapps.user_authn.cookies import set_logged_in_cookies
from openedx.core.djangoapps.user_authn.views.register import REGISTER_USER, \
    record_registration_attributions
from openedx.features.partners.helpers import get_partner_recommended_courses
from pytz import UTC
from student.models import Registration, create_comments_service_user, UserProfile
from util.json_request import JsonResponse

from .forms import Give2AsiaAccountCreationForm

log = logging.getLogger("edx.student")
AUDIT_LOG = logging.getLogger("audit")


def g2a_dashboard(request):
    # TODO: The argument must be dynamic after integration of LP-1632
    courses = get_partner_recommended_courses('give2asia')
    return render_to_response('partners/g2a/dashboard.html', {'recommended_courses': courses})


class Give2AsiaRegistrationView(RegistrationViewCustom):
    """
    This class handles registration flow for give2asia users. It inherit some basic functionality from original (normal)
    registration flow
    """

    def get(self, request, partner):
        pass

    def post(self, request, partner):

        registration_data = request.POST.copy()

        # Adding basic data, required to bypass onboarding flow
        registration_data['organization_name'] = partner.label
        registration_data['year_of_birth'] = 2000
        registration_data['level_of_education'] = 'IWRNS'
        registration_data['partners_opt_in'] = ''

        # validate data provided by end user
        account_creation_form = Give2AsiaAccountCreationForm(data=registration_data, tos_required=True)
        if not account_creation_form.is_valid():
            return JsonResponse({"Error": dict(account_creation_form.errors.items())}, status=400)

        registration_data['email'] = account_creation_form.cleaned_data["email"]
        registration_data['username'] = account_creation_form.cleaned_data["username"]
        registration_data['password'] = account_creation_form.cleaned_data["password"]
        registration_data['organization_name'] = account_creation_form.cleaned_data["organization_name"]

        name = account_creation_form.cleaned_data["name"]
        registration_data['name'] = name

        name_split = name.split(" ", 1)
        registration_data['first_name'] = name_split[0]
        registration_data['last_name'] = name_split[1]

        try:
            # Create models for user, UserProfile and UserExtendedProfile
            user = create_account_with_params_custom(request, registration_data)
            self.save_user_utm_info(user)
            save_user_partner_network_consent(user, registration_data['partners_opt_in'])
        except Exception:
            return JsonResponse({"Error": {"reason": "User registration failed"}}, status=400)

        RegistrationType.objects.create(choice=1, user=request.user)
        response = JsonResponse({"success": True})
        set_logged_in_cookies(request, response, user)
        return response


def create_account_with_params_custom(request, params):
    # Copy params so we can modify it; we can't just do dict(params) because if
    # params is request.POST, that results in a dict containing lists of values
    params = dict(params.items())

    extended_profile_fields = configuration_helpers.get_value('extended_profile_fields', [])

    # Perform operations within a transaction that are critical to account creation
    with transaction.atomic():
        try:
            # Create user and activate it
            user = User(
                username=params['username'],
                email=params["email"],
                first_name=params['first_name'],
                last_name=params['last_name'],
                is_active=True,
            )
            user.set_password(params["password"])
            registration = Registration()

            user.save()
            registration.register(user)
        except Exception:  # pylint: disable=broad-except
            log.exception("User creation failed for user {username}.".format(username=params['username']))
            raise

        try:
            # Update User profile

            profile_fields = [
                "name", "level_of_education", "gender", "country", "year_of_birth"
            ]
            profile = UserProfile(
                user=user,
                **{key: params.get(key) for key in profile_fields}
            )

            # Return a dictionary containing the extended_profile_fields and values
            extended_profile_data = {
                key: value
                for key, value in params.items() if key in extended_profile_fields and value is not None
            }

            if extended_profile_data:
                profile.meta = json.dumps(extended_profile_data)
            profile.save()
        except Exception:  # pylint: disable=broad-except
            log.exception("UserProfile creation failed for user {id}.".format(id=user.id))
            raise

        try:
            # create User Extended Profile
            extended_profile = UserExtendedProfile.objects.create(user=user)
            extended_profile.english_proficiency = 'IWRNS'
            extended_profile.start_month_year = '11/2019'
            extended_profile.is_interests_data_submitted = True

            # Assign Give2Asia organization to new user
            # Give2AsiaAccountCreationForm will handle if organization not found
            organization_to_assign = Organization.objects.filter(label__iexact=params['organization_name']).first()
            extended_profile.organization = organization_to_assign
            extended_profile.save()
        except Exception:  # pylint: disable=broad-except
            log.exception("User extended profile creation failed for user {id}.".format(id=user.id))
            raise ValidationError()

        try:
            user_email_preferences, created = EmailPreference.objects.get_or_create(user=user)
            user_email_preferences.opt_in = False
            user_email_preferences.save()
        except Exception:  # pylint: disable=broad-except
            log.exception("User email preferences creation failed for user {id}.".format(id=user.id))
            raise ValidationError()

    # Perform operations that are non-critical parts of account creation
    preferences_api.set_user_preference(user, LANGUAGE_KEY, get_language())

    if settings.FEATURES.get('ENABLE_DISCUSSION_EMAIL_DIGEST'):
        try:
            enable_notifications(user)
        except Exception:  # pylint: disable=broad-except
            log.exception("Enable discussion notifications failed for user {id}.".format(id=user.id))

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
                'yearOfBirth': profile.year_of_birth or datetime.datetime.now(UTC).year,
                'education': profile.level_of_education_display,
                'address': profile.mailing_address,
                'gender': profile.gender_display,
                'country': unicode(profile.country),
            }
        ]
        analytics.identify(*identity_args)
        analytics.track(
            user.id,
            "edx.bi.user.account.registered",
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

    # Announce registration
    REGISTER_USER.send(sender=None, user=user, registration=registration)

    create_comments_service_user(user)

    registration.activate()

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
        AUDIT_LOG.info(u"Login success on new account creation - {0}".format(new_user.username))

    return new_user
