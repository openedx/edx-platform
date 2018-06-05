"""
An API for retrieving user account information.

For additional information and historical context, see:
https://openedx.atlassian.net/wiki/display/TNL/User+API
"""
import datetime
import logging
from functools import wraps

import pytz
from consent.models import DataSharingConsent
from django.contrib.auth import authenticate, get_user_model, logout
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.db import transaction
from django.utils.translation import ugettext as _
from edx_ace import ace
from edx_ace.recipient import Recipient
from edx_rest_framework_extensions.authentication import JwtAuthentication
from enterprise.models import EnterpriseCourseEnrollment, EnterpriseCustomerUser, PendingEnterpriseCustomerUser
from integrated_channels.degreed.models import DegreedLearnerDataTransmissionAudit
from integrated_channels.sap_success_factors.models import SapSuccessFactorsLearnerDataTransmissionAudit
from rest_framework import permissions, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from six import text_type
from social_django.models import UserSocialAuth
from wiki.models import ArticleRevision
from wiki.models.pluginbase import RevisionPluginRevision

from entitlements.models import CourseEntitlement
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
from openedx.core.djangoapps.ace_common.template_context import get_base_template_context
from openedx.core.djangoapps.api_admin.models import ApiAccessRequest
from openedx.core.djangoapps.credit.models import CreditRequirementStatus, CreditRequest
from openedx.core.djangoapps.course_groups.models import UnregisteredLearnerCohortAssignments
from openedx.core.djangoapps.profile_images.images import remove_profile_images
from openedx.core.djangoapps.user_api.accounts.image_helpers import get_profile_image_names, set_has_profile_image
from openedx.core.djangoapps.user_api.preferences.api import update_email_opt_in
from openedx.core.djangolib.oauth2_retirement_utils import retire_dot_oauth2_models, retire_dop_oauth2_models
from openedx.core.lib.api.authentication import (
    OAuth2AuthenticationAllowInactiveUser,
    SessionAuthenticationAllowInactiveUser
)
from openedx.core.lib.api.parsers import MergePatchParser
from survey.models import SurveyAnswer
from student.models import (
    CourseEnrollment,
    ManualEnrollmentAudit,
    PasswordHistory,
    PendingNameChange,
    CourseEnrollmentAllowed,
    PendingEmailChange,
    Registration,
    User,
    UserProfile,
    get_potentially_retired_user_by_username,
    get_retired_email_by_email,
    get_retired_username_by_username,
    is_username_retired
)
from student.views.login import AuthFailedError, LoginFailures

from ..errors import AccountUpdateError, AccountValidationError, UserNotAuthorized, UserNotFound
from ..models import (
    RetirementState,
    RetirementStateError,
    UserOrgTag,
    UserRetirementPartnerReportingStatus,
    UserRetirementStatus
)
from .api import get_account_settings, update_account_settings
from .permissions import CanDeactivateUser, CanRetireUser
from .serializers import UserRetirementPartnerReportSerializer, UserRetirementStatusSerializer
from .signals import USER_RETIRE_MAILINGS
from ..message_types import DeletionNotificationMessage

log = logging.getLogger(__name__)

USER_PROFILE_PII = {
    'name': '',
    'meta': '',
    'location': '',
    'year_of_birth': None,
    'gender': None,
    'mailing_address': None,
    'city': None,
    'country': None,
    'bio': None,
}


def request_requires_username(function):
    """
    Requires that a ``username`` key containing a truthy value exists in
    the ``request.data`` attribute of the decorated function.
    """
    @wraps(function)
    def wrapper(self, request):  # pylint: disable=missing-docstring
        username = request.data.get('username', None)
        if not username:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data={'message': text_type('The user was not specified.')}
            )
        return function(self, request)
    return wrapper


class AccountViewSet(ViewSet):
    """
        **Use Cases**

            Get or update a user's account information. Updates are supported
            only through merge patch.

        **Example Requests**

            GET /api/user/v1/me[?view=shared]
            GET /api/user/v1/accounts?usernames={username1,username2}[?view=shared]
            GET /api/user/v1/accounts/{username}/[?view=shared]

            PATCH /api/user/v1/accounts/{username}/{"key":"value"} "application/merge-patch+json"

        **Response Values for GET requests to the /me endpoint**
            If the user is not logged in, an HTTP 401 "Not Authorized" response
            is returned.

            Otherwise, an HTTP 200 "OK" response is returned. The response
            contains the following value:

            * username: The username associated with the account.

        **Response Values for GET requests to /accounts endpoints**

            If no user exists with the specified username, an HTTP 404 "Not
            Found" response is returned.

            If the user makes the request for her own account, or makes a
            request for another account and has "is_staff" access, an HTTP 200
            "OK" response is returned. The response contains the following
            values.

            * bio: null or textual representation of user biographical
              information ("about me").
            * country: An ISO 3166 country code or null.
            * date_joined: The date the account was created, in the string
              format provided by datetime. For example, "2014-08-26T17:52:11Z".
            * email: Email address for the user. New email addresses must be confirmed
              via a confirmation email, so GET does not reflect the change until
              the address has been confirmed.
            * gender: One of the following values:

                * null
                * "f"
                * "m"
                * "o"

            * goals: The textual representation of the user's goals, or null.
            * is_active: Boolean representation of whether a user is active.
            * language: The user's preferred language, or null.
            * language_proficiencies: Array of language preferences. Each
              preference is a JSON object with the following keys:

                * "code": string ISO 639-1 language code e.g. "en".

            * level_of_education: One of the following values:

                * "p": PhD or Doctorate
                * "m": Master's or professional degree
                * "b": Bachelor's degree
                * "a": Associate's degree
                * "hs": Secondary/high school
                * "jhs": Junior secondary/junior high/middle school
                * "el": Elementary/primary school
                * "none": None
                * "o": Other
                * null: The user did not enter a value

            * mailing_address: The textual representation of the user's mailing
              address, or null.
            * name: The full name of the user.
            * profile_image: A JSON representation of a user's profile image
              information. This representation has the following keys.

                * "has_image": Boolean indicating whether the user has a profile
                  image.
                * "image_url_*": Absolute URL to various sizes of a user's
                  profile image, where '*' matches a representation of the
                  corresponding image size, such as 'small', 'medium', 'large',
                  and 'full'. These are configurable via PROFILE_IMAGE_SIZES_MAP.

            * requires_parental_consent: True if the user is a minor
              requiring parental consent.
            * social_links: Array of social links. Each
              preference is a JSON object with the following keys:

                * "platform": A particular social platform, ex: 'facebook'
                * "social_link": The link to the user's profile on the particular platform

            * username: The username associated with the account.
            * year_of_birth: The year the user was born, as an integer, or null.
            * account_privacy: The user's setting for sharing her personal
              profile. Possible values are "all_users" or "private".
            * accomplishments_shared: Signals whether badges are enabled on the
              platform and should be fetched.

            For all text fields, plain text instead of HTML is supported. The
            data is stored exactly as specified. Clients must HTML escape
            rendered values to avoid script injections.

            If a user who does not have "is_staff" access requests account
            information for a different user, only a subset of these fields is
            returned. The returns fields depend on the
            ACCOUNT_VISIBILITY_CONFIGURATION configuration setting and the
            visibility preference of the user for whom data is requested.

            Note that a user can view which account fields they have shared
            with other users by requesting their own username and providing
            the "view=shared" URL parameter.

        **Response Values for PATCH**

            Users can only modify their own account information. If the
            requesting user does not have the specified username and has staff
            access, the request returns an HTTP 403 "Forbidden" response. If
            the requesting user does not have staff access, the request
            returns an HTTP 404 "Not Found" response to avoid revealing the
            existence of the account.

            If no user exists with the specified username, an HTTP 404 "Not
            Found" response is returned.

            If "application/merge-patch+json" is not the specified content
            type, a 415 "Unsupported Media Type" response is returned.

            If validation errors prevent the update, this method returns a 400
            "Bad Request" response that includes a "field_errors" field that
            lists all error messages.

            If a failure at the time of the update prevents the update, a 400
            "Bad Request" error is returned. The JSON collection contains
            specific errors.

            If the update is successful, updated user account data is returned.
    """
    authentication_classes = (
        OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser, JwtAuthentication
    )
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MergePatchParser,)

    def get(self, request):
        """
        GET /api/user/v1/me
        """
        return Response({'username': request.user.username})

    def list(self, request):
        """
        GET /api/user/v1/accounts?username={username1,username2}
        """
        usernames = request.GET.get('username')
        try:
            if usernames:
                usernames = usernames.strip(',').split(',')
            account_settings = get_account_settings(
                request, usernames, view=request.query_params.get('view'))
        except UserNotFound:
            return Response(status=status.HTTP_403_FORBIDDEN if request.user.is_staff else status.HTTP_404_NOT_FOUND)

        return Response(account_settings)

    def retrieve(self, request, username):
        """
        GET /api/user/v1/accounts/{username}/
        """
        try:
            account_settings = get_account_settings(
                request, [username], view=request.query_params.get('view'))
        except UserNotFound:
            return Response(status=status.HTTP_403_FORBIDDEN if request.user.is_staff else status.HTTP_404_NOT_FOUND)

        return Response(account_settings[0])

    def partial_update(self, request, username):
        """
        PATCH /api/user/v1/accounts/{username}/

        Note that this implementation is the "merge patch" implementation proposed in
        https://tools.ietf.org/html/rfc7396. The content_type must be "application/merge-patch+json" or
        else an error response with status code 415 will be returned.
        """
        try:
            with transaction.atomic():
                update_account_settings(request.user, request.data, username=username)
                account_settings = get_account_settings(request, [username])[0]
        except UserNotAuthorized:
            return Response(status=status.HTTP_403_FORBIDDEN if request.user.is_staff else status.HTTP_404_NOT_FOUND)
        except UserNotFound:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except AccountValidationError as err:
            return Response({"field_errors": err.field_errors}, status=status.HTTP_400_BAD_REQUEST)
        except AccountUpdateError as err:
            return Response(
                {
                    "developer_message": err.developer_message,
                    "user_message": err.user_message
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(account_settings)


class AccountDeactivationView(APIView):
    """
    Account deactivation viewset. Currently only supports POST requests.
    Only admins can deactivate accounts.
    """
    authentication_classes = (JwtAuthentication, )
    permission_classes = (permissions.IsAuthenticated, CanDeactivateUser)

    def post(self, request, username):
        """
        POST /api/user/v1/accounts/{username}/deactivate/

        Marks the user as having no password set for deactivation purposes.
        """
        _set_unusable_password(User.objects.get(username=username))
        return Response(get_account_settings(request, [username])[0])


class AccountRetireMailingsView(APIView):
    """
    Part of the retirement API, accepts POSTs to unsubscribe a user
    from all email lists.
    """
    authentication_classes = (JwtAuthentication, )
    permission_classes = (permissions.IsAuthenticated, CanRetireUser)

    def post(self, request):
        """
        POST /api/user/v1/accounts/{username}/retire_mailings/

        Allows an administrative user to take the following actions
        on behalf of an LMS user:
        -  Update UserOrgTags to opt the user out of org emails
        -  Call Sailthru API to force opt-out the user from all email lists
        """
        username = request.data['username']

        try:
            retirement = UserRetirementStatus.get_retirement_for_retirement_action(username)

            with transaction.atomic():
                # Take care of org emails first, using the existing API for consistency
                for preference in UserOrgTag.objects.filter(user=retirement.user, key='email-optin'):
                    update_email_opt_in(retirement.user, preference.org, False)

                # This signal allows lms' email_marketing and other 3rd party email
                # providers to unsubscribe the user as well
                USER_RETIRE_MAILINGS.send(
                    sender=self.__class__,
                    email=retirement.original_email,
                    new_email=retirement.retired_email,
                    user=retirement.user
                )

            return Response(status=status.HTTP_204_NO_CONTENT)
        except UserRetirementStatus.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception as exc:  # pylint: disable=broad-except
            return Response(text_type(exc), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeactivateLogoutView(APIView):
    """
    POST /api/user/v1/accounts/deactivate_logout/
    {
        "password": "example_password",
    }

    **POST Parameters**

      A POST request must include the following parameter.

      * password: Required. The current password of the user being deactivated.

    **POST Response Values**

     If the request does not specify a username or submits a username
     for a non-existent user, the request returns an HTTP 404 "Not Found"
     response.

     If a user who is not a superuser tries to deactivate a user,
     the request returns an HTTP 403 "Forbidden" response.

     If the specified user is successfully deactivated, the request
     returns an HTTP 204 "No Content" response.

     If an unanticipated error occurs, the request returns an
     HTTP 500 "Internal Server Error" response.

    Allows an LMS user to take the following actions:
    -  Change the user's password permanently to Django's unusable password
    -  Log the user out
    - Create a row in the retirement table for that user
    """
    authentication_classes = (SessionAuthentication, JwtAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )

    def post(self, request):
        """
        POST /api/user/v1/accounts/deactivate_logout/

        Marks the user as having no password set for deactivation purposes,
        and logs the user out.
        """
        user_model = get_user_model()
        try:
            # Get the username from the request and check that it exists
            verify_user_password_response = self._verify_user_password(request)
            if verify_user_password_response.status_code != status.HTTP_204_NO_CONTENT:
                return verify_user_password_response
            with transaction.atomic():
                UserRetirementStatus.create_retirement(request.user)
                # Unlink LMS social auth accounts
                UserSocialAuth.objects.filter(user_id=request.user.id).delete()
                # Change LMS password & email
                user_email = request.user.email
                request.user.email = get_retired_email_by_email(request.user.email)
                request.user.save()
                _set_unusable_password(request.user)
                # TODO: Unlink social accounts & change password on each IDA.
                # Remove the activation keys sent by email to the user for account activation.
                Registration.objects.filter(user=request.user).delete()
                # Add user to retirement queue.
                # Delete OAuth tokens associated with the user.
                retire_dop_oauth2_models(request.user)
                retire_dot_oauth2_models(request.user)

                try:
                    # Send notification email to user
                    site = Site.objects.get_current()
                    notification_context = get_base_template_context(site)
                    notification_context.update({'full_name': request.user.profile.name})
                    notification = DeletionNotificationMessage().personalize(
                        recipient=Recipient(username='', email_address=user_email),
                        language=request.user.profile.language,
                        user_context=notification_context,
                    )
                    ace.send(notification)
                except Exception as exc:
                    log.exception('Error sending out deletion notification email')
                    raise

                # Log the user out.
                logout(request)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except KeyError:
            return Response(u'Username not specified.', status=status.HTTP_404_NOT_FOUND)
        except user_model.DoesNotExist:
            return Response(
                u'The user "{}" does not exist.'.format(request.user.username), status=status.HTTP_404_NOT_FOUND
            )
        except Exception as exc:  # pylint: disable=broad-except
            return Response(text_type(exc), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _verify_user_password(self, request):
        """
        If the user is logged in and we want to verify that they have submitted the correct password
        for a major account change (for example, retiring this user's account).

        Args:
            request (HttpRequest): A request object where the password should be included in the POST fields.
        """
        try:
            self._check_excessive_login_attempts(request.user)
            user = authenticate(username=request.user.username, password=request.POST['password'], request=request)
            if user:
                if LoginFailures.is_feature_enabled():
                    LoginFailures.clear_lockout_counter(user)
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                self._handle_failed_authentication(request.user)
        except AuthFailedError as err:
            return Response(text_type(err), status=status.HTTP_403_FORBIDDEN)
        except Exception as err:  # pylint: disable=broad-except
            return Response(u"Could not verify user password: {}".format(err), status=status.HTTP_400_BAD_REQUEST)

    def _check_excessive_login_attempts(self, user):
        """
        See if account has been locked out due to excessive login failures
        """
        if user and LoginFailures.is_feature_enabled():
            if LoginFailures.is_user_locked_out(user):
                raise AuthFailedError(_('This account has been temporarily locked due '
                                        'to excessive login failures. Try again later.'))

    def _handle_failed_authentication(self, user):
        """
        Handles updating the failed login count, inactive user notifications, and logging failed authentications.
        """
        if user and LoginFailures.is_feature_enabled():
            LoginFailures.increment_lockout_counter(user)

        raise AuthFailedError(_('Email or password is incorrect.'))


def _set_unusable_password(user):
    """
    Helper method for the shared functionality of setting a user's
    password to the unusable password, thus deactivating the account.
    """
    user.set_unusable_password()
    user.save()


class AccountRetirementPartnerReportView(ViewSet):
    """
    Provides API endpoints for managing partner reporting of retired
    users.
    """
    authentication_classes = (JwtAuthentication,)
    permission_classes = (permissions.IsAuthenticated, CanRetireUser,)
    parser_classes = (JSONParser,)
    serializer_class = UserRetirementStatusSerializer

    def _get_orgs_for_user(self, user):
        """
        Returns a set of orgs that the user has enrollments with
        """
        orgs = set()
        for enrollment in user.courseenrollment_set.all():
            org = enrollment.course.org

            # Org can concievably be blank or this bogus default value
            if org and org != 'outdated_entry':
                orgs.add(enrollment.course.org)
        return orgs

    def retirement_partner_report(self, request):  # pylint: disable=unused-argument
        """
        POST /api/user/v1/accounts/retirement_partner_report/

        Returns the list of UserRetirementPartnerReportingStatus users
        that are not already being processed and updates their status
        to indicate they are currently being processed.
        """
        retirement_statuses = UserRetirementPartnerReportingStatus.objects.filter(
            is_being_processed=False
        ).order_by('id')

        retirements = [
            {
                'original_username': retirement.original_username,
                'original_email': retirement.original_email,
                'original_name': retirement.original_name,
                'orgs': self._get_orgs_for_user(retirement.user)
            }
            for retirement in retirement_statuses
        ]

        serializer = UserRetirementPartnerReportSerializer(retirements, many=True)

        retirement_statuses.update(is_being_processed=True)

        return Response(serializer.data)

    def retirement_partner_cleanup(self, request):
        """
        DELETE /api/user/v1/accounts/retirement_partner_report/

        [{'original_username': 'user1'}, {'original_username': 'user2'}, ...]

        Deletes UserRetirementPartnerReportingStatus objects for a list of users
        that have been reported on.
        """
        usernames = [u['original_username'] for u in request.data]

        if not usernames:
            return Response('No original_usernames given.', status=status.HTTP_400_BAD_REQUEST)

        retirement_statuses = UserRetirementPartnerReportingStatus.objects.filter(
            is_being_processed=True,
            original_username__in=usernames
        )

        if len(usernames) != len(retirement_statuses):
            return Response(
                '{} original_usernames given, only {} found!'.format(len(usernames), len(retirement_statuses)),
                status=status.HTTP_400_BAD_REQUEST
            )

        retirement_statuses.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class AccountRetirementStatusView(ViewSet):
    """
    Provides API endpoints for managing the user retirement process.
    """
    authentication_classes = (JwtAuthentication,)
    permission_classes = (permissions.IsAuthenticated, CanRetireUser,)
    parser_classes = (JSONParser,)
    serializer_class = UserRetirementStatusSerializer

    def retirement_queue(self, request):
        """
        GET /api/user/v1/accounts/retirement_queue/
        {'cool_off_days': 7, 'states': ['PENDING', 'COMPLETE']}

        Returns the list of RetirementStatus users in the given states that were
        created in the retirement queue at least `cool_off_days` ago.
        """
        try:
            cool_off_days = int(request.GET['cool_off_days'])
            if cool_off_days < 0:
                raise RetirementStateError('Invalid argument for cool_off_days, must be greater than 0.')

            states = request.GET.getlist('states')
            if not states:
                raise RetirementStateError('Param "states" required with at least one state.')

            state_objs = RetirementState.objects.filter(state_name__in=states)
            if state_objs.count() != len(states):
                found = [s.state_name for s in state_objs]
                raise RetirementStateError('Unknown state. Requested: {} Found: {}'.format(states, found))

            earliest_datetime = datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=cool_off_days)

            retirements = UserRetirementStatus.objects.select_related(
                'user', 'current_state', 'last_state'
            ).filter(
                current_state__in=state_objs, created__lt=earliest_datetime
            ).order_by(
                'id'
            )
            serializer = UserRetirementStatusSerializer(retirements, many=True)
            return Response(serializer.data)
        # This should only occur on the int() converstion of cool_off_days at this point
        except ValueError:
            return Response('Invalid cool_off_days, should be integer.', status=status.HTTP_400_BAD_REQUEST)
        except KeyError as exc:
            return Response('Missing required parameter: {}'.format(text_type(exc)), status=status.HTTP_400_BAD_REQUEST)
        except RetirementStateError as exc:
            return Response(text_type(exc), status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, username):  # pylint: disable=unused-argument
        """
        GET /api/user/v1/accounts/{username}/retirement_status/
        Returns the RetirementStatus of a given user, or 404 if that row
        doesn't exist.
        """
        try:
            user = get_potentially_retired_user_by_username(username)
            retirement = UserRetirementStatus.objects.select_related(
                'user', 'current_state', 'last_state'
            ).get(user=user)
            serializer = UserRetirementStatusSerializer(instance=retirement)
            return Response(serializer.data)
        except (UserRetirementStatus.DoesNotExist, User.DoesNotExist):
            return Response(status=status.HTTP_404_NOT_FOUND)

    @request_requires_username
    def partial_update(self, request):
        """
        PATCH /api/user/v1/accounts/update_retirement_status/

        {
            'username': 'user_to_retire',
            'new_state': 'LOCKING_COMPLETE',
            'response': 'User account locked and logged out.'
        }

        Updates the RetirementStatus row for the given user to the new
        status, and append any messages to the message log.

        Note that this implementation DOES NOT use the "merge patch"
        implementation seen in AccountViewSet. Slumber, the project
        we use to power edx-rest-api-client, does not currently support
        it. The content type for this request is 'application/json'.
        """
        try:
            username = request.data['username']
            retirement = UserRetirementStatus.objects.get(original_username=username)
            retirement.update_state(request.data)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except UserRetirementStatus.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except RetirementStateError as exc:
            return Response(text_type(exc), status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:  # pylint: disable=broad-except
            return Response(text_type(exc), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LMSAccountRetirementView(ViewSet):
    """
    Provides an API endpoint for retiring a user in the LMS.
    """
    authentication_classes = (JwtAuthentication,)
    permission_classes = (permissions.IsAuthenticated, CanRetireUser,)
    parser_classes = (JSONParser,)

    @request_requires_username
    def post(self, request):
        """
        POST /api/user/v1/accounts/retire_misc/

        {
            'username': 'user_to_retire'
        }

        Retires the user with the given username in the LMS.
        """

        username = request.data['username']
        if is_username_retired(username):
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            retirement = UserRetirementStatus.get_retirement_for_retirement_action(username)
            RevisionPluginRevision.retire_user(retirement.user)
            ArticleRevision.retire_user(retirement.user)
            PendingNameChange.delete_by_user_value(retirement.user, field='user')
            PasswordHistory.retire_user(retirement.user.id)
            course_enrollments = CourseEnrollment.objects.filter(user=retirement.user)
            ManualEnrollmentAudit.retire_manual_enrollments(course_enrollments, retirement.retired_email)

            CreditRequest.retire_user(retirement.original_username, retirement.retired_username)
            ApiAccessRequest.retire_user(retirement.user)
            CreditRequirementStatus.retire_user(retirement.user.username)
            SurveyAnswer.retire_user(retirement.user.id)

        except UserRetirementStatus.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except RetirementStateError as exc:
            return Response(text_type(exc), status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:  # pylint: disable=broad-except
            return Response(text_type(exc), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(status=status.HTTP_204_NO_CONTENT)


class AccountRetirementView(ViewSet):
    """
    Provides API endpoint for retiring a user.
    """
    authentication_classes = (JwtAuthentication,)
    permission_classes = (permissions.IsAuthenticated, CanRetireUser,)
    parser_classes = (JSONParser,)

    @request_requires_username
    def post(self, request):
        """
        POST /api/user/v1/accounts/retire/

        {
            'username': 'user_to_retire'
        }

        Retires the user with the given username.  This includes
        retiring this username, the associates email address, and
        any other PII associated with this user.
        """
        username = request.data['username']
        if is_username_retired(username):
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            retirement_status = UserRetirementStatus.get_retirement_for_retirement_action(username)
            user = retirement_status.user
            retired_username = retirement_status.retired_username or get_retired_username_by_username(username)
            retired_email = retirement_status.retired_email or get_retired_email_by_email(user.email)
            original_email = retirement_status.original_email

            # Retire core user/profile information
            self.clear_pii_from_userprofile(user)
            self.delete_users_profile_images(user)
            self.delete_users_country_cache(user)

            # Retire data from Enterprise models
            self.retire_users_data_sharing_consent(username, retired_username)
            self.retire_sapsf_data_transmission(user)
            self.retire_degreed_data_transmission(user)
            self.retire_user_from_pending_enterprise_customer_user(user, retired_email)
            self.retire_entitlement_support_detail(user)

            # Retire misc. models that may contain PII of this user
            SoftwareSecurePhotoVerification.retire_user(user.id)
            PendingEmailChange.delete_by_user_value(user, field='user')
            UserOrgTag.delete_by_user_value(user, field='user')

            # Retire any objects linked to the user via their original email
            CourseEnrollmentAllowed.delete_by_user_value(original_email, field='email')
            UnregisteredLearnerCohortAssignments.delete_by_user_value(original_email, field='email')

            # TODO: Password Reset links - https://openedx.atlassian.net/browse/PLAT-2104
            # TODO: Delete OAuth2 records - https://openedx.atlassian.net/browse/EDUCATOR-2703

            user.first_name = ''
            user.last_name = ''
            user.is_active = False
            user.username = retired_username
            user.save()
        except UserRetirementStatus.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except RetirementStateError as exc:
            return Response(text_type(exc), status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:  # pylint: disable=broad-except
            return Response(text_type(exc), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def clear_pii_from_userprofile(user):
        """
        For the given user, sets all of the user's profile fields to some retired value.
        This also deletes all ``SocialLink`` objects associated with this user's profile.
        """
        for model_field, value_to_assign in USER_PROFILE_PII.iteritems():
            setattr(user.profile, model_field, value_to_assign)

        user.profile.save()
        user.profile.social_links.all().delete()

    @staticmethod
    def delete_users_profile_images(user):
        set_has_profile_image(user.username, False)
        names_of_profile_images = get_profile_image_names(user.username)
        remove_profile_images(names_of_profile_images)

    @staticmethod
    def delete_users_country_cache(user):
        cache_key = UserProfile.country_cache_key_name(user.id)
        cache.delete(cache_key)

    @staticmethod
    def retire_users_data_sharing_consent(username, retired_username):
        DataSharingConsent.objects.filter(username=username).update(username=retired_username)

    @staticmethod
    def retire_sapsf_data_transmission(user):
        for ent_user in EnterpriseCustomerUser.objects.filter(user_id=user.id):
            for enrollment in EnterpriseCourseEnrollment.objects.filter(
                enterprise_customer_user=ent_user
            ):
                audits = SapSuccessFactorsLearnerDataTransmissionAudit.objects.filter(
                    enterprise_course_enrollment_id=enrollment.id
                )
                audits.update(sapsf_user_id='')

    @staticmethod
    def retire_degreed_data_transmission(user):
        for ent_user in EnterpriseCustomerUser.objects.filter(user_id=user.id):
            for enrollment in EnterpriseCourseEnrollment.objects.filter(
                enterprise_customer_user=ent_user
            ):
                audits = DegreedLearnerDataTransmissionAudit.objects.filter(
                    enterprise_course_enrollment_id=enrollment.id
                )
                audits.update(degreed_user_email='')

    @staticmethod
    def retire_user_from_pending_enterprise_customer_user(user, retired_email):
        PendingEnterpriseCustomerUser.objects.filter(user_email=user.email).update(user_email=retired_email)

    @staticmethod
    def retire_entitlement_support_detail(user):
        """
        Updates all CourseEntitleSupportDetail records for the given
        user to have an empty ``comments`` field.
        """
        for entitlement in CourseEntitlement.objects.filter(user_id=user.id):
            entitlement.courseentitlementsupportdetail_set.all().update(comments='')
