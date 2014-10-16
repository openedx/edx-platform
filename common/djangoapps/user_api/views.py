"""HTTP end-points for the User API. """
import json

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import authentication
from rest_framework import filters
from rest_framework import generics
from rest_framework import permissions
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.exceptions import ParseError
from django_countries.countries import COUNTRIES
from user_api.serializers import UserSerializer, UserPreferenceSerializer
from user_api.models import UserPreference, UserProfile
from django_comment_common.models import Role
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from user_api.api import account as account_api, profile as profile_api
from user_api.helpers import FormDescription, shim_student_view, require_post_params


class ApiKeyHeaderPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        """
        Check for permissions by matching the configured API key and header

        If settings.DEBUG is True and settings.EDX_API_KEY is not set or None,
        then allow the request. Otherwise, allow the request if and only if
        settings.EDX_API_KEY is set and the X-Edx-Api-Key HTTP header is
        present in the request and matches the setting.
        """
        api_key = getattr(settings, "EDX_API_KEY", None)
        return (
            (settings.DEBUG and api_key is None) or
            (api_key is not None and request.META.get("HTTP_X_EDX_API_KEY") == api_key)
        )


class LoginSessionView(APIView):
    """HTTP end-points for logging in users. """

    def get(self, request):
        """Return a description of the login form.

        This decouples clients from the API definition:
        if the API decides to modify the form, clients won't need
        to be updated.

        See `user_api.helpers.FormDescription` for examples
        of the JSON-encoded form description.

        Arguments:
            request (HttpRequest)

        Returns:
            HttpResponse

        """
        form_desc = FormDescription("post", reverse("user_api_login_session"))

        form_desc.add_field(
            "email",
            label=_(u"E-mail"),
            placeholder=_(u"example: username@domain.com"),
            instructions=_(
                u"This is the e-mail address you used to register with {platform}"
            ).format(platform=settings.PLATFORM_NAME),
            restrictions={
                "min_length": account_api.EMAIL_MIN_LENGTH,
                "max_length": account_api.EMAIL_MAX_LENGTH,
            }
        )

        form_desc.add_field(
            "password",
            label=_(u"Password"),
            restrictions={
                "min_length": account_api.PASSWORD_MIN_LENGTH,
                "max_length": account_api.PASSWORD_MAX_LENGTH,
            }
        )

        return HttpResponse(form_desc.to_json(), content_type="application/json")

    @method_decorator(ensure_csrf_cookie)
    @method_decorator(require_post_params(["email", "password"]))
    def post(self, request):
        """Log in a user.

        Arguments:
            request (HttpRequest)

        Returns:
            HttpResponse: 200 on success
            HttpResponse: 400 if the request is not valid.
            HttpResponse: 403 if authentication failed.
            HttpResponse: 302 if redirecting to another page.

        Example Usage:

            POST /user_api/v1/login_session
            with POST params `email` and `password`

            200 OK

        """
        # For the initial implementation, shim the existing login view
        # from the student Django app.
        from student.views import login_user
        return shim_student_view(login_user, check_logged_in=True)(request)


class RegistrationView(APIView):
    """HTTP end-points for creating a new user. """

    DEFAULT_FIELDS = ["email", "name", "username", "password"]

    EXTRA_FIELDS = [
        "city", "country", "level_of_education", "gender",
        "year_of_birth", "mailing_address", "goals",
    ]

    def __init__(self, *args, **kwargs):
        super(RegistrationView, self).__init__(*args, **kwargs)

        # Map field names to the instance method used to add the field to the form
        self.field_handlers = {}
        for field_name in (self.DEFAULT_FIELDS + self.EXTRA_FIELDS):
            handler = getattr(self, "_add_{field_name}_field".format(field_name=field_name))
            self.field_handlers[field_name] = handler

    def get(self, request):
        """Return a description of the registration form.

        This decouples clients from the API definition:
        if the API decides to modify the form, clients won't need
        to be updated.

        This is especially important for the registration form,
        since different edx-platform installations might
        collect different demographic information.

        See `user_api.helpers.FormDescription` for examples
        of the JSON-encoded form description.

        Arguments:
            request (HttpRequest)

        Returns:
            HttpResponse

        """
        form_desc = FormDescription("post", reverse("user_api_registration"))

        # Default fields are always required
        for field_name in self.DEFAULT_FIELDS:
            self.field_handlers[field_name](form_desc, required=True)

        # Extra fields configured in Django settings
        # may be required, optional, or hidden
        for field_name in self.EXTRA_FIELDS:
            field_setting = settings.REGISTRATION_EXTRA_FIELDS.get(field_name, "hidden")
            handler = self.field_handlers[field_name]

            if field_setting in ["required", "optional"]:
                handler(form_desc, required=(field_setting == "required"))
            elif field_setting != "hidden":
                msg = u"Setting REGISTRATION_EXTRA_FIELDS values must be either required, optional, or hidden."
                raise ImproperlyConfigured(msg)

        return HttpResponse(form_desc.to_json(), content_type="application/json")

    @method_decorator(ensure_csrf_cookie)
    @method_decorator(require_post_params(DEFAULT_FIELDS))
    def post(self, request):
        """Create the user's account.

        Arguments:
            request (HTTPRequest)

        Returns:
            HttpResponse: 200 on success
            HttpResponse: 400 if the request is not valid.
            HttpResponse: 302 if redirecting to another page.

        """
        # Backwards compatability
        # We used to validate that the users had checked
        # "honor code" and "terms of service"
        # on the registration form.  Now we rely on the client
        # to display this to users and validate that they
        # agree before making the request to this service.
        request.POST["honor_code"] = "true"
        request.POST["terms_of_service"] = "true"

        # Handle duplicate username/email
        conflicts = account_api.check_account_exists(
            username=request.POST.get('username'),
            email=request.POST.get('email')
        )
        if conflicts:
            return HttpResponse(
                status=409,
                content=json.dumps(conflicts),
                content_type="application/json"
            )

        # For the initial implementation, shim the existing login view
        # from the student Django app.
        from student.views import create_account
        return shim_student_view(create_account)(request)

    def _add_email_field(self, form_desc, required=True):
        form_desc.add_field(
            "email",
            label=_(u"E-mail"),
            placeholder=_(u"example: username@domain.com"),
            instructions=_(
                u"This is the e-mail address you used to register with {platform}"
            ).format(platform=settings.PLATFORM_NAME),
            restrictions={
                "min_length": account_api.EMAIL_MIN_LENGTH,
                "max_length": account_api.EMAIL_MAX_LENGTH,
            },
            required=required
        )

    def _add_name_field(self, form_desc, required=True):
        form_desc.add_field(
            "name",
            label=_(u"Full Name"),
            instructions=_(u"Needed for any certificates you may earn"),
            restrictions={
                "max_length": profile_api.FULL_NAME_MAX_LENGTH,
            },
            required=required
        )

    def _add_username_field(self, form_desc, required=True):
        form_desc.add_field(
            "username",
            label=_(u"Public Username"),
            instructions=_(u"Will be shown in any discussions or forums you participate in (cannot be changed)"),
            restrictions={
                "min_length": account_api.USERNAME_MIN_LENGTH,
                "max_length": account_api.USERNAME_MAX_LENGTH,
            },
            required=required
        )

    def _add_password_field(self, form_desc, required=True):
        form_desc.add_field(
            "password",
            label=_(u"Password"),
            restrictions={
                "min_length": account_api.PASSWORD_MIN_LENGTH,
                "max_length": account_api.PASSWORD_MAX_LENGTH,
            },
            required=required
        )

    def _add_level_of_education_field(self, form_desc, required=True):
        form_desc.add_field(
            "level_of_education",
            label=_("Highest Level of Education Completed"),
            field_type="select",
            options=self._options_with_default(UserProfile.LEVEL_OF_EDUCATION_CHOICES),
            required=required
        )

    def _add_gender_field(self, form_desc, required=True):
        form_desc.add_field(
            "gender",
            label=_("Gender"),
            field_type="select",
            options=self._options_with_default(UserProfile.GENDER_CHOICES),
            required=required
        )

    def _add_year_of_birth_field(self, form_desc, required=True):
        options = [(unicode(year), unicode(year)) for year in UserProfile.VALID_YEARS]
        form_desc.add_field(
            "year_of_birth",
            label=_("Year of Birth"),
            field_type="select",
            options=self._options_with_default(options),
            required=required
        )

    def _add_mailing_address_field(self, form_desc, required=True):
        form_desc.add_field(
            "mailing_address",
            label=_("Mailing Address"),
            field_type="textarea",
            required=required
        )

    def _add_goals_field(self, form_desc, required=True):
        form_desc.add_field(
            "goals",
            label=_("Please share with us your reasons for registering with edX"),
            field_type="textarea",
            required=required
        )

    def _add_city_field(self, form_desc, required=True):
        form_desc.add_field(
            "city",
            label=_("City"),
            required=required
        )

    def _add_country_field(self, form_desc, required=True):
        options = [
            (country_code, unicode(country_name))
            for country_code, country_name in COUNTRIES
        ]
        form_desc.add_field(
            "country",
            label=_("Country"),
            field_type="select",
            options=self._options_with_default(options),
            required=required
        )

    def _options_with_default(self, options):
        """Include a default option as the first option. """
        return (
            [("", "--")] + list(options)
        )


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (ApiKeyHeaderPermission,)
    queryset = User.objects.all().prefetch_related("preferences")
    serializer_class = UserSerializer
    paginate_by = 10
    paginate_by_param = "page_size"


class ForumRoleUsersListView(generics.ListAPIView):
    """
    Forum roles are represented by a list of user dicts
    """
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (ApiKeyHeaderPermission,)
    serializer_class = UserSerializer
    paginate_by = 10
    paginate_by_param = "page_size"

    def get_queryset(self):
        """
        Return a list of users with the specified role/course pair
        """
        name = self.kwargs['name']
        course_id_string = self.request.QUERY_PARAMS.get('course_id')
        if not course_id_string:
            raise ParseError('course_id must be specified')
        course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id_string)
        role = Role.objects.get_or_create(course_id=course_id, name=name)[0]
        users = role.users.all()
        return users


class UserPreferenceViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (ApiKeyHeaderPermission,)
    queryset = UserPreference.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ("key", "user")
    serializer_class = UserPreferenceSerializer
    paginate_by = 10
    paginate_by_param = "page_size"


class PreferenceUsersListView(generics.ListAPIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (ApiKeyHeaderPermission,)
    serializer_class = UserSerializer
    paginate_by = 10
    paginate_by_param = "page_size"

    def get_queryset(self):
        return User.objects.filter(preferences__key=self.kwargs["pref_key"]).prefetch_related("preferences")
