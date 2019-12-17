import analytics
import json
from datetime import datetime
from logging import getLogger

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models.signals import post_save
from django.http import Http404
from rest_framework import status
from django.utils.translation import get_language
from edxmako.shortcuts import render_to_response
from eventtracking import tracker
from notification_prefs.views import enable_notifications
from pytz import UTC
from util.json_request import JsonResponse

from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.user_api.preferences import api as preferences_api
from openedx.core.djangoapps.user_authn.cookies import set_logged_in_cookies
from openedx.core.djangoapps.user_authn.views.register import REGISTER_USER, record_registration_attributions
from openedx.features.partners.helpers import get_partner_recommended_courses
from openedx.features.partners.models import PartnerUser

from lms.djangoapps.philu_overrides.user_api.views import RegistrationViewCustom
from lms.djangoapps.onboarding.models import EmailPreference, Organization, PartnerNetwork, UserExtendedProfile
from philu_overrides.user_api.views import LoginSessionViewCustom
from nodebb.helpers import update_nodebb_for_user_status
from student.models import Registration, UserProfile

from . import constants as g2a_constants
from .forms import Give2AsiaAccountCreationForm

log = getLogger("edx.student")
AUDIT_LOG = getLogger("audit")


def dashboard(request, partner_slug):
    courses = get_partner_recommended_courses(partner_slug)
    return render_to_response('features/partners/g2a/dashboard.html', {'recommended_courses': courses,
                                                                       'slug': partner_slug})


class Give2AsiaRegistrationView(RegistrationViewCustom):
    """
    This class handles registration flow for give2asia users. It inherit some basic functionality from original (normal)
    registration flow
    """

    def get(self, request, partner):
        # Overriding get method to suppress corresponding method of parent class
        raise Http404

    def post(self, request, partner):
        registration_data = request.POST.copy()

        # validate data provided by end user
        account_creation_form = Give2AsiaAccountCreationForm(data=registration_data, tos_required=True)
        if not account_creation_form.is_valid():
            return JsonResponse({"Error": dict(account_creation_form.errors.items())}, status=400)

        account_creation_form.clean_registration_data(registration_data)
        try:
            # Create or update models for User, UserProfile,
            # UserExtendedProfile, Organization, PartnerUser and EmailPreference
            user = create_account_with_params_custom(request, registration_data, partner)
            self.save_user_utm_info(user)
        except Exception as err:
            error_message = {"Error": {"reason": "User registration failed due to {}".format(repr(err))}}
            log.exception(error_message)
            return JsonResponse(error_message, status=400)

        response = JsonResponse({"success": True})
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
                email=params["email"],
                first_name=first_name,
                last_name=last_name,
                is_active=True,
            )
            user.set_password(params["password"])
            registration = Registration()

            user.save()
            registration.register(user)
        except Exception as err:  # pylint: disable=broad-except
            log.exception("User creation failed for user {username}".format(username=params['username']), repr(err))
            raise

        extended_profile_data = g2a_constants.G2A_EXTENDED_PROFILE_DEFAULT_DATA
        extended_profile_data[g2a_constants.START_MONTH_YEAR_KEY] = datetime.now().strftime('%m/%Y')

        user_profile_data = g2a_constants.G2A_USER_PROFILE_DEFAULT_DATA
        user_profile_data['name'] = '{} {}'.format(first_name, last_name)

        try:
            # Create user profile
            profile = UserProfile(user=user, **user_profile_data)
            profile.meta = json.dumps(extended_profile_data)
            profile.save()

            # We have to manually trigger the post_save so that profile is synced on nodebb
            post_save.send(UserProfile, instance=profile, created=False)

        except Exception as err:  # pylint: disable=broad-except
            log.exception("UserProfile creation failed for user {id}.".format(id=user.id), repr(err))
            raise

        try:
            organization_data = g2a_constants.G2A_ORGANIZATION_DEFAULT_DATA
            organization_data[g2a_constants.ORG_TYPE_KEY] = PartnerNetwork.NON_PROFIT_ORG_TYPE_CODE

            organization_name = params['organization_name']
            organization_to_assign = Organization.objects.filter(label__iexact=organization_name).first()
            if not organization_to_assign:
                # Create organization if not already exists and make user first learner
                organization_to_assign = Organization.objects.create(label=organization_name, **organization_data)
                organization_to_assign.save()

            # create User Extended Profile
            extended_profile = UserExtendedProfile.objects.create(
                user=user, organization=organization_to_assign, **extended_profile_data
            )

            extended_profile.save()
        except Exception as err:  # pylint: disable=broad-except
            log.exception("User extended profile creation failed for user {id}.".format(id=user.id), repr(err))
            raise

        try:
            # create a bridge between user and partner
            partner_user = PartnerUser.objects.create(user=user, partner=partner)
            partner_user.save()
        except Exception as err:  # pylint: disable=broad-except
            log.exception("partner_user creation failed for user {id}, partner {slug}"
                          .format(id=user.id, slug=partner.slug), repr(err))
            raise

        try:
            user_email_preferences, created = EmailPreference.objects.get_or_create(user=user)
            user_email_preferences.opt_in = g2a_constants.OPT_IN_DATA
            user_email_preferences.save()
        except Exception as err:  # pylint: disable=broad-except
            log.exception("User email preferences creation failed for user {id}.".format(id=user.id), repr(err))
            raise

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
                'yearOfBirth': profile.year_of_birth or datetime.now(UTC).year,
                'education': profile.level_of_education_display,
                'address': profile.mailing_address,
                'gender': profile.gender_display,
                'country': unicode(profile.country),
            }
        ]

        if hasattr(settings, 'MAILCHIMP_NEW_USER_LIST_ID'):
            identity_args.append({
                "MailChimp": {
                    "listId": settings.MAILCHIMP_NEW_USER_LIST_ID
                }
            })

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

    # Since all required data corresponding to new user is saved in relevant models
    # request NodeBB to activate registered user
    update_nodebb_for_user_status(params['username'])

    # Announce registration
    REGISTER_USER.send(sender=None, user=user, registration=registration)
    if not registration.user.is_active:
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


class LoginSessionViewG2A(LoginSessionViewCustom):
    """
    Inherited from LoginSessionViewCustom to keep the existing flow for login
    and extend the functionality to affiliate the user with Give2Asia if not already done
    """

    def post(self, request, partner):

        response = super(LoginSessionViewG2A, self).post(request)

        if response.status_code == status.HTTP_200_OK:
            user = request.user
            try:
                PartnerUser.objects.get_or_create(partner=partner, user=user)
            except Exception as ex:
                log.error("Failed to affiliate {user} with {partner} due to exception {exp}".format(
                    user=user.username, partner=partner.slug, exp=ex.message)
                )
        return response
