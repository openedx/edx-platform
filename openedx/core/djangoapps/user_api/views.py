"""HTTP end-points for the User API. """

import json
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django_filters.rest_framework import DjangoFilterBackend
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser

from opaque_keys import InvalidKeyError
from opaque_keys.edx import locator
from opaque_keys.edx.keys import CourseKey
from rest_framework import generics, status, viewsets
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from social_django.models import UserSocialAuth

from common.djangoapps.student.models import (
    email_exists_or_retired,
    username_exists_or_retired,
)
from common.djangoapps.third_party_auth.models import OAuth2ProviderConfig
from openedx.core.djangoapps.django_comment_common.models import Role
from openedx.core.djangoapps.safe_sessions.middleware import mark_user_change_as_expected
from openedx.core.djangoapps.user_api.models import UserPreference
from openedx.core.djangoapps.user_api.preferences.api import get_country_time_zones, update_email_opt_in
from openedx.core.djangoapps.user_api.serializers import (
    CountryTimeZoneSerializer,
    ProfileSerializer,
    UserPreferenceSerializer,
    UserCreateSerializer,
    UserSerializer,
)
from openedx.core.djangoapps.user_authn.views.register import create_account_with_params
from openedx.core.lib.api.permissions import ApiKeyHeaderPermission
from openedx.core.lib.api.view_utils import require_post_params


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    DRF class for interacting with the User ORM object
    """

    permission_classes = (ApiKeyHeaderPermission,)
    queryset = User.objects.all().prefetch_related("preferences").select_related("profile")
    serializer_class = UserSerializer
    paginate_by = 10
    paginate_by_param = "page_size"


class ForumRoleUsersListView(generics.ListAPIView):
    """
    Forum roles are represented by a list of user dicts
    """

    permission_classes = (ApiKeyHeaderPermission,)
    serializer_class = UserSerializer
    paginate_by = 10
    paginate_by_param = "page_size"

    def get_queryset(self):
        """
        Return a list of users with the specified role/course pair
        """
        name = self.kwargs["name"]
        course_id_string = self.request.query_params.get("course_id")
        if not course_id_string:
            raise ParseError("course_id must be specified")
        course_id = CourseKey.from_string(course_id_string)
        role = Role.objects.get_or_create(course_id=course_id, name=name)[0]
        users = role.users.prefetch_related("preferences").select_related("profile").all()
        return users


class UserPreferenceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    DRF class for interacting with the UserPreference ORM
    """

    permission_classes = (ApiKeyHeaderPermission,)
    queryset = UserPreference.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("key", "user")
    serializer_class = UserPreferenceSerializer
    paginate_by = 10
    paginate_by_param = "page_size"


class PreferenceUsersListView(generics.ListAPIView):
    """
    DRF class for listing a user's preferences
    """

    permission_classes = (ApiKeyHeaderPermission,)
    serializer_class = UserSerializer
    paginate_by = 10
    paginate_by_param = "page_size"

    def get_queryset(self):
        return (
            User.objects.filter(preferences__key=self.kwargs["pref_key"])
            .prefetch_related("preferences")
            .select_related("profile")
        )


class UpdateEmailOptInPreference(APIView):
    """View for updating the email opt in preference."""

    authentication_classes = (SessionAuthenticationAllowInactiveUser,)
    permission_classes = (IsAuthenticated,)

    @method_decorator(require_post_params(["course_id", "email_opt_in"]))
    @method_decorator(ensure_csrf_cookie)
    def post(self, request):
        """Post function for updating the email opt in preference.

        Allows the modification or creation of the email opt in preference at an
        organizational level.

        Args:
            request (Request): The request should contain the following POST parameters:
                * course_id: The slash separated course ID. Used to determine the organization
                    for this preference setting.
                * email_opt_in: "True" or "False" to determine if the user is opting in for emails from
                    this organization. If the string does not match "True" (case insensitive) it will
                    assume False.

        """
        course_id = request.data["course_id"]
        try:
            org = locator.CourseLocator.from_string(course_id).org
        except InvalidKeyError:
            return HttpResponse(status=400, content=f"No course '{course_id}' found", content_type="text/plain")
        # Only check for true. All other values are False.
        email_opt_in = request.data["email_opt_in"].lower() == "true"
        update_email_opt_in(request.user, org, email_opt_in)
        return HttpResponse(status=status.HTTP_200_OK)


class CountryTimeZoneListView(generics.ListAPIView):
    """
    **Use Cases**

        Retrieves a list of all time zones, by default, or common time zones for country, if given

        The country is passed in as its ISO 3166-1 Alpha-2 country code as an
        optional 'country_code' argument. The country code is also case-insensitive.

    **Example Requests**

        GET /api/user/v1/preferences/time_zones/

        GET /api/user/v1/preferences/time_zones/?country_code=FR

    **Example GET Response**

        If the request is successful, an HTTP 200 "OK" response is returned along with a
        list of time zone dictionaries for all time zones or just for time zones commonly
        used in a country, if given.

        Each time zone dictionary contains the following values.

            * time_zone: The name of the time zone.
            * description: The display version of the time zone
    """

    serializer_class = CountryTimeZoneSerializer
    paginator = None

    def get_queryset(self):
        country_code = self.request.GET.get("country_code", None)
        return get_country_time_zones(country_code)


class CreateUserAccountWithoutPasswordView(APIView):
    """
    Create or update a user account.
    """

    _error_dict = {
        "username": "Username is a required parameter.",
        "email": "Email is a required parameter.",
        "gender": "Gender must be one of 'm' (Male), 'f' (Female) "
                  "or 'o' (Other. Default if parameter is missing)",
        "uid": "Uid is a required parameter."
    }

    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (IsAdminUser,)

    @method_decorator(transaction.non_atomic_requests)
    def dispatch(self, request, *args, **kwargs):
        """
        Decorate with `non_atomic_requests` to work on newer versions of platform.
        """
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        """
        Create a user by the email and the username.
        """
        data = dict(request.data.items())
        data['honor_code'] = "True"
        data['terms_of_service'] = "True"
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        full_name = request.data.get('full_name', '')

        try:
            email = self._check_available_required_params(request.data.get('email'), "email")
            username = self._check_available_required_params(request.data.get('username'),
                                                             "username")
            uid = self._check_available_required_params(request.data.get('uid'), "uid")
            data['gender'] = self._check_available_required_params(
                request.data.get('gender', 'o'), "gender", ['m', 'f', 'o']
            )
            if self._check_account_exists(username=username, email=email):
                return Response(data={"error_message": "User already exists"},
                                status=status.HTTP_409_CONFLICT)
            if UserSocialAuth.objects.filter(uid=uid).exists():
                return Response(
                    data={"error_message": "Parameter 'uid' isn't unique."},
                    status=status.HTTP_409_CONFLICT
                )
            # if full_name provided add it to profile data
            if full_name:
                data['name'] = full_name
            else:
                data['name'] = (
                    f"{first_name} {last_name}".strip()
                    if first_name or last_name
                    else username
                )
            profile_meta = {
                'first_name': first_name,
                'last_name': last_name
            }
            data['meta'] = json.dumps(profile_meta)
            UserCreateSerializer().run_validation(data)
            ProfileSerializer().run_validation(data)
            data['first_name'] = first_name
            data['last_name'] = last_name
            data['password'] = User.objects.make_random_password()
            for param in ('is_active', 'allow_certificate'):
                data[param] = data.get(param, True)
            user = create_account_with_params(request, data)
            mark_user_change_as_expected(None)
            for idp_name in OAuth2ProviderConfig.key_values('backend_name', flat=True):
                UserSocialAuth.objects.create(user=user, provider=idp_name, uid=uid)
            user = UserSerializer().update(user, data)
            ProfileSerializer().update(user.profile, data)
        except (ValueError, ValidationError, DjangoValidationError) as e:
            if isinstance(e, ValidationError):
                message = e.detail
            else:
                message = str(e)
            return Response(
                data={"error_message": message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(data={'user_id': user.id, 'username': username}, status=status.HTTP_200_OK)

    def _check_available_required_params(self, parameter, parameter_name, values_list=None):
        """
        Check required parameter is correct.

        If parameter isn't correct ValueError is raised.

        :param parameter: object
        :param parameter_name: string. Parameter's name
        :param values_list: List of values

        :return: parameter
        """
        if not parameter or (values_list
                             and isinstance(values_list, list)
                             and parameter not in values_list):
            raise ValueError(self._error_dict[parameter_name].format(value=parameter))
        return parameter

    def _check_account_exists(self, username=None, email=None):
        """
        Check if account exists by username or email.

        :param username: string
        :param email: string
        :return: boolean
        """
        if username is not None and username_exists_or_retired(username):
            return True
        if email is not None and email_exists_or_retired(email):
            return True
        return False
