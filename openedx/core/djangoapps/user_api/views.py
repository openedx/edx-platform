"""HTTP end-points for the User API. """
import copy
from openedx.core.lib.api.permissions import ApiKeyHeaderPermission
from opaque_keys import InvalidKeyError
import third_party_auth

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from opaque_keys.edx import locator
from rest_framework import authentication
from rest_framework import filters
from rest_framework import generics
from rest_framework import status
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.exceptions import ParseError
from django_countries import countries
from django_comment_common.models import Role
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from edxmako.shortcuts import marketing_link

from util.authentication import SessionAuthenticationAllowInactiveUser
from .api import account as account_api, profile as profile_api
from .helpers import FormDescription, shim_student_view, require_post_params
from .models import UserPreference, UserProfile
from .serializers import UserSerializer, UserPreferenceSerializer


class LoginSessionView(APIView):
    """HTTP end-points for logging in users. """

    # This end-point is available to anonymous users,
    # so do not require authentication.
    authentication_classes = []

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):  # pylint: disable=unused-argument
        """Return a description of the login form.

        This decouples clients from the API definition:
        if the API decides to modify the form, clients won't need
        to be updated.

        See `user_api.helpers.FormDescription` for examples
        of the JSON-encoded form description.

        Returns:
            HttpResponse

        """
        form_desc = FormDescription("post", reverse("user_api_login_session"))

        # Translators: This label appears above a field on the login form
        # meant to hold the user's email address.
        email_label = _(u"Email")

        # Translators: This example email address is used as a placeholder in
        # a field on the login form meant to hold the user's email address.
        email_placeholder = _(u"username@domain.com")

        # Translators: These instructions appear on the login form, immediately
        # below a field meant to hold the user's email address.
        email_instructions = _(
            u"The email address you used to register with {platform_name}"
        ).format(platform_name=settings.PLATFORM_NAME)

        form_desc.add_field(
            "email",
            field_type="email",
            label=email_label,
            placeholder=email_placeholder,
            instructions=email_instructions,
            restrictions={
                "min_length": account_api.EMAIL_MIN_LENGTH,
                "max_length": account_api.EMAIL_MAX_LENGTH,
            }
        )

        # Translators: This label appears above a field on the login form
        # meant to hold the user's password.
        password_label = _(u"Password")

        form_desc.add_field(
            "password",
            label=password_label,
            field_type="password",
            restrictions={
                "min_length": account_api.PASSWORD_MIN_LENGTH,
                "max_length": account_api.PASSWORD_MAX_LENGTH,
            }
        )

        return HttpResponse(form_desc.to_json(), content_type="application/json")

    @method_decorator(require_post_params(["email", "password"]))
    @method_decorator(csrf_protect)
    def post(self, request):
        """Log in a user.

        You must send all required form fields with the request.

        You can optionally send an `analytics` param with a JSON-encoded
        object with additional info to include in the login analytics event.
        Currently, the only supported field is "enroll_course_id" to indicate
        that the user logged in while enrolling in a particular course.

        Arguments:
            request (HttpRequest)

        Returns:
            HttpResponse: 200 on success
            HttpResponse: 400 if the request is not valid.
            HttpResponse: 403 if authentication failed.
                403 with content "third-party-auth" if the user
                has successfully authenticated with a third party provider
                but does not have a linked account.
            HttpResponse: 302 if redirecting to another page.

        Example Usage:

            POST /user_api/v1/login_session
            with POST params `email`, `password`, and `remember`.

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
        "city",
        "country",
        "gender",
        "year_of_birth",
        "level_of_education",
        "mailing_address",
        "goals",
        "honor_code",
        "terms_of_service",
    ]

    # This end-point is available to anonymous users,
    # so do not require authentication.
    authentication_classes = []

    def _is_field_visible(self, field_name):
        """Check whether a field is visible based on Django settings. """
        return self._extra_fields_setting.get(field_name) in ["required", "optional"]

    def _is_field_required(self, field_name):
        """Check whether a field is required based on Django settings. """
        return self._extra_fields_setting.get(field_name) == "required"

    def __init__(self, *args, **kwargs):
        super(RegistrationView, self).__init__(*args, **kwargs)

        # Backwards compatibility: Honor code is required by default, unless
        # explicitly set to "optional" in Django settings.
        self._extra_fields_setting = copy.deepcopy(settings.REGISTRATION_EXTRA_FIELDS)
        self._extra_fields_setting["honor_code"] = self._extra_fields_setting.get("honor_code", "required")

        # Check that the setting is configured correctly
        for field_name in self.EXTRA_FIELDS:
            if self._extra_fields_setting.get(field_name, "hidden") not in ["required", "optional", "hidden"]:
                msg = u"Setting REGISTRATION_EXTRA_FIELDS values must be either required, optional, or hidden."
                raise ImproperlyConfigured(msg)

        # Map field names to the instance method used to add the field to the form
        self.field_handlers = {}
        for field_name in (self.DEFAULT_FIELDS + self.EXTRA_FIELDS):
            handler = getattr(self, "_add_{field_name}_field".format(field_name=field_name))
            self.field_handlers[field_name] = handler

    @method_decorator(ensure_csrf_cookie)
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
        self._apply_third_party_auth_overrides(request, form_desc)

        # Default fields are always required
        for field_name in self.DEFAULT_FIELDS:
            self.field_handlers[field_name](form_desc, required=True)

        # Extra fields configured in Django settings
        # may be required, optional, or hidden
        for field_name in self.EXTRA_FIELDS:
            if self._is_field_visible(field_name):
                self.field_handlers[field_name](
                    form_desc,
                    required=self._is_field_required(field_name)
                )

        return HttpResponse(form_desc.to_json(), content_type="application/json")

    @method_decorator(require_post_params(DEFAULT_FIELDS))
    @method_decorator(csrf_protect)
    def post(self, request):
        """Create the user's account.

        You must send all required form fields with the request.

        You can optionally send an `analytics` param with a JSON-encoded
        object with additional info to include in the registration analytics event.
        Currently, the only supported field is "enroll_course_id" to indicate
        that the user registered while enrolling in a particular course.

        Arguments:
            request (HTTPRequest)

        Returns:
            HttpResponse: 200 on success
            HttpResponse: 400 if the request is not valid.
            HttpResponse: 302 if redirecting to another page.

        """
        email = request.POST.get('email')
        username = request.POST.get('username')

        # Handle duplicate email/username
        conflicts = account_api.check_account_exists(email=email, username=username)
        if conflicts:
            if all(conflict in conflicts for conflict in ['email', 'username']):
                # Translators: This message is shown to users who attempt to create a new
                # account using both an email address and a username associated with an
                # existing account.
                error_msg = _(
                    u"It looks like {email_address} and {username} belong to an existing account. Try again with a different email address and username."
                ).format(email_address=email, username=username)
            elif 'email' in conflicts:
                # Translators: This message is shown to users who attempt to create a new
                # account using an email address associated with an existing account.
                error_msg = _(
                    u"It looks like {email_address} belongs to an existing account. Try again with a different email address."
                ).format(email_address=email)
            else:
                # Translators: This message is shown to users who attempt to create a new
                # account using a username associated with an existing account.
                error_msg = _(
                    u"It looks like {username} belongs to an existing account. Try again with a different username."
                ).format(username=username)

            return HttpResponse(
                status=409,
                content=error_msg,
                content_type="text/plain"
            )

        # For the initial implementation, shim the existing login view
        # from the student Django app.
        from student.views import create_account
        return shim_student_view(create_account)(request)

    def _add_email_field(self, form_desc, required=True):
        """Add an email field to a form description.

        Arguments:
            form_desc: A form description

        Keyword Arguments:
            required (Boolean): Whether this field is required; defaults to True

        """
        # Translators: This label appears above a field on the registration form
        # meant to hold the user's email address.
        email_label = _(u"Email")

        # Translators: This example email address is used as a placeholder in
        # a field on the registration form meant to hold the user's email address.
        email_placeholder = _(u"username@domain.com")

        form_desc.add_field(
            "email",
            field_type="email",
            label=email_label,
            placeholder=email_placeholder,
            restrictions={
                "min_length": account_api.EMAIL_MIN_LENGTH,
                "max_length": account_api.EMAIL_MAX_LENGTH,
            },
            required=required
        )

    def _add_name_field(self, form_desc, required=True):
        """Add a name field to a form description.

        Arguments:
            form_desc: A form description

        Keyword Arguments:
            required (Boolean): Whether this field is required; defaults to True

        """
        # Translators: This label appears above a field on the registration form
        # meant to hold the user's full name.
        name_label = _(u"Full name")

        # Translators: These instructions appear on the registration form, immediately
        # below a field meant to hold the user's full name.
        name_instructions = _(u"The name that will appear on your certificates")

        form_desc.add_field(
            "name",
            label=name_label,
            instructions=name_instructions,
            restrictions={
                "max_length": profile_api.FULL_NAME_MAX_LENGTH,
            },
            required=required
        )

    def _add_username_field(self, form_desc, required=True):
        """Add a username field to a form description.

        Arguments:
            form_desc: A form description

        Keyword Arguments:
            required (Boolean): Whether this field is required; defaults to True

        """
        # Translators: This label appears above a field on the registration form
        # meant to hold the user's public username.
        username_label = _(u"Public username")

        # Translators: These instructions appear on the registration form, immediately
        # below a field meant to hold the user's public username.
        username_instructions = _(
            u"The name that will identify you in your courses"
        )

        form_desc.add_field(
            "username",
            label=username_label,
            instructions=username_instructions,
            restrictions={
                "min_length": account_api.USERNAME_MIN_LENGTH,
                "max_length": account_api.USERNAME_MAX_LENGTH,
            },
            required=required
        )

    def _add_password_field(self, form_desc, required=True):
        """Add a password field to a form description.

        Arguments:
            form_desc: A form description

        Keyword Arguments:
            required (Boolean): Whether this field is required; defaults to True

        """
        # Translators: This label appears above a field on the registration form
        # meant to hold the user's password.
        password_label = _(u"Password")

        form_desc.add_field(
            "password",
            label=password_label,
            field_type="password",
            restrictions={
                "min_length": account_api.PASSWORD_MIN_LENGTH,
                "max_length": account_api.PASSWORD_MAX_LENGTH,
            },
            required=required
        )

    def _add_level_of_education_field(self, form_desc, required=True):
        """Add a level of education field to a form description.

        Arguments:
            form_desc: A form description

        Keyword Arguments:
            required (Boolean): Whether this field is required; defaults to True

        """
        # Translators: This label appears above a dropdown menu on the registration
        # form used to select the user's highest completed level of education.
        education_level_label = _(u"Highest level of education completed")

        form_desc.add_field(
            "level_of_education",
            label=education_level_label,
            field_type="select",
            options=UserProfile.LEVEL_OF_EDUCATION_CHOICES,
            include_default_option=True,
            required=required
        )

    def _add_gender_field(self, form_desc, required=True):
        """Add a gender field to a form description.

        Arguments:
            form_desc: A form description

        Keyword Arguments:
            required (Boolean): Whether this field is required; defaults to True

        """
        # Translators: This label appears above a dropdown menu on the registration
        # form used to select the user's gender.
        gender_label = _(u"Gender")

        form_desc.add_field(
            "gender",
            label=gender_label,
            field_type="select",
            options=UserProfile.GENDER_CHOICES,
            include_default_option=True,
            required=required
        )

    def _add_year_of_birth_field(self, form_desc, required=True):
        """Add a year of birth field to a form description.

        Arguments:
            form_desc: A form description

        Keyword Arguments:
            required (Boolean): Whether this field is required; defaults to True

        """
        # Translators: This label appears above a dropdown menu on the registration
        # form used to select the user's year of birth.
        yob_label = _(u"Year of birth")

        options = [(unicode(year), unicode(year)) for year in UserProfile.VALID_YEARS]
        form_desc.add_field(
            "year_of_birth",
            label=yob_label,
            field_type="select",
            options=options,
            include_default_option=True,
            required=required
        )

    def _add_mailing_address_field(self, form_desc, required=True):
        """Add a mailing address field to a form description.

        Arguments:
            form_desc: A form description

        Keyword Arguments:
            required (Boolean): Whether this field is required; defaults to True

        """
        # Translators: This label appears above a field on the registration form
        # meant to hold the user's mailing address.
        mailing_address_label = _(u"Mailing address")

        form_desc.add_field(
            "mailing_address",
            label=mailing_address_label,
            field_type="textarea",
            required=required
        )

    def _add_goals_field(self, form_desc, required=True):
        """Add a goals field to a form description.

        Arguments:
            form_desc: A form description

        Keyword Arguments:
            required (Boolean): Whether this field is required; defaults to True

        """
        # Translators: This phrase appears above a field on the registration form
        # meant to hold the user's reasons for registering with edX.
        goals_label = _(
            u"Tell us why you're interested in {platform_name}"
        ).format(platform_name=settings.PLATFORM_NAME)

        form_desc.add_field(
            "goals",
            label=goals_label,
            field_type="textarea",
            required=required
        )

    def _add_city_field(self, form_desc, required=True):
        """Add a city field to a form description.

        Arguments:
            form_desc: A form description

        Keyword Arguments:
            required (Boolean): Whether this field is required; defaults to True

        """
        # Translators: This label appears above a field on the registration form
        # which allows the user to input the city in which they live.
        city_label = _(u"City")

        form_desc.add_field(
            "city",
            label=city_label,
            required=required
        )

    def _add_country_field(self, form_desc, required=True):
        """Add a country field to a form description.

        Arguments:
            form_desc: A form description

        Keyword Arguments:
            required (Boolean): Whether this field is required; defaults to True

        """
        # Translators: This label appears above a dropdown menu on the registration
        # form used to select the country in which the user lives.
        country_label = _(u"Country")

        sorted_countries = sorted(
            countries.countries, key=lambda(__, name): unicode(name)
        )
        options = [
            (country_code, unicode(country_name))
            for country_code, country_name in sorted_countries
        ]

        error_msg = _(u"Please select your Country.")

        form_desc.add_field(
            "country",
            label=country_label,
            field_type="select",
            options=options,
            include_default_option=True,
            required=required,
            error_messages={
                "required": error_msg
            }
        )

    def _add_honor_code_field(self, form_desc, required=True):
        """Add an honor code field to a form description.

        Arguments:
            form_desc: A form description

        Keyword Arguments:
            required (Boolean): Whether this field is required; defaults to True

        """
        # Separate terms of service and honor code checkboxes
        if self._is_field_visible("terms_of_service"):
            terms_text = _(u"Honor Code")

        # Combine terms of service and honor code checkboxes
        else:
            # Translators: This is a legal document users must agree to
            # in order to register a new account.
            terms_text = _(u"Terms of Service and Honor Code")

        terms_link = u"<a href=\"{url}\">{terms_text}</a>".format(
            url=marketing_link("HONOR"),
            terms_text=terms_text
        )

        # Translators: "Terms of Service" is a legal document users must agree to
        # in order to register a new account.
        label = _(
            u"I agree to the {platform_name} {terms_of_service}."
        ).format(
            platform_name=settings.PLATFORM_NAME,
            terms_of_service=terms_link
        )

        # Translators: "Terms of Service" is a legal document users must agree to
        # in order to register a new account.
        error_msg = _(
            u"You must agree to the {platform_name} {terms_of_service}."
        ).format(
            platform_name=settings.PLATFORM_NAME,
            terms_of_service=terms_link
        )

        form_desc.add_field(
            "honor_code",
            label=label,
            field_type="checkbox",
            default=False,
            required=required,
            error_messages={
                "required": error_msg
            }
        )

    def _add_terms_of_service_field(self, form_desc, required=True):
        """Add a terms of service field to a form description.

        Arguments:
            form_desc: A form description

        Keyword Arguments:
            required (Boolean): Whether this field is required; defaults to True

        """
        # Translators: This is a legal document users must agree to
        # in order to register a new account.
        terms_text = _(u"Terms of Service")
        terms_link = u"<a href=\"{url}\">{terms_text}</a>".format(
            url=marketing_link("TOS"),
            terms_text=terms_text
        )

        # Translators: "Terms of service" is a legal document users must agree to
        # in order to register a new account.
        label = _(
            u"I agree to the {platform_name} {terms_of_service}."
        ).format(
            platform_name=settings.PLATFORM_NAME,
            terms_of_service=terms_link
        )

        # Translators: "Terms of service" is a legal document users must agree to
        # in order to register a new account.
        error_msg = _(
            u"You must agree to the {platform_name} {terms_of_service}."
        ).format(
            platform_name=settings.PLATFORM_NAME,
            terms_of_service=terms_link
        )

        form_desc.add_field(
            "terms_of_service",
            label=label,
            field_type="checkbox",
            default=False,
            required=required,
            error_messages={
                "required": error_msg
            }
        )

    def _apply_third_party_auth_overrides(self, request, form_desc):
        """Modify the registration form if the user has authenticated with a third-party provider.

        If a user has successfully authenticated with a third-party provider,
        but does not yet have an account with EdX, we want to fill in
        the registration form with any info that we get from the
        provider.

        This will also hide the password field, since we assign users a default
        (random) password on the assumption that they will be using
        third-party auth to log in.

        Arguments:
            request (HttpRequest): The request for the registration form, used
                to determine if the user has successfully authenticated
                with a third-party provider.

            form_desc (FormDescription): The registration form description

        """
        if third_party_auth.is_enabled():
            running_pipeline = third_party_auth.pipeline.get(request)
            if running_pipeline:
                current_provider = third_party_auth.provider.Registry.get_by_backend_name(running_pipeline.get('backend'))

                # Override username / email / full name
                field_overrides = current_provider.get_register_form_data(
                    running_pipeline.get('kwargs')
                )

                for field_name in self.DEFAULT_FIELDS:
                    if field_name in field_overrides:
                        form_desc.override_field_properties(
                            field_name, default=field_overrides[field_name]
                        )

                # Hide the password field
                form_desc.override_field_properties(
                    "password",
                    default="",
                    field_type="hidden",
                    required=False,
                    label="",
                    instructions="",
                    restrictions={}
                )


class PasswordResetView(APIView):
    """HTTP end-point for GETting a description of the password reset form. """

    # This end-point is available to anonymous users,
    # so do not require authentication.
    authentication_classes = []

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):  # pylint: disable=unused-argument
        """Return a description of the password reset form.

        This decouples clients from the API definition:
        if the API decides to modify the form, clients won't need
        to be updated.

        See `user_api.helpers.FormDescription` for examples
        of the JSON-encoded form description.

        Returns:
            HttpResponse

        """
        form_desc = FormDescription("post", reverse("password_change_request"))

        # Translators: This label appears above a field on the password reset
        # form meant to hold the user's email address.
        email_label = _(u"Email")

        # Translators: This example email address is used as a placeholder in
        # a field on the password reset form meant to hold the user's email address.
        email_placeholder = _(u"username@domain.com")

        # Translators: These instructions appear on the password reset form,
        # immediately below a field meant to hold the user's email address.
        email_instructions = _(
            u"The email address you used to register with {platform_name}"
        ).format(platform_name=settings.PLATFORM_NAME)

        form_desc.add_field(
            "email",
            field_type="email",
            label=email_label,
            placeholder=email_placeholder,
            instructions=email_instructions,
            restrictions={
                "min_length": account_api.EMAIL_MIN_LENGTH,
                "max_length": account_api.EMAIL_MAX_LENGTH,
            }
        )

        return HttpResponse(form_desc.to_json(), content_type="application/json")


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


class UpdateEmailOptInPreference(APIView):
    """View for updating the email opt in preference. """
    authentication_classes = (SessionAuthenticationAllowInactiveUser,)

    @method_decorator(require_post_params(["course_id", "email_opt_in"]))
    @method_decorator(ensure_csrf_cookie)
    def post(self, request):
        """ Post function for updating the email opt in preference.

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
        course_id = request.DATA['course_id']
        try:
            org = locator.CourseLocator.from_string(course_id).org
        except InvalidKeyError:
            return HttpResponse(
                status=400,
                content="No course '{course_id}' found".format(course_id=course_id),
                content_type="text/plain"
            )
        # Only check for true. All other values are False.
        email_opt_in = request.DATA['email_opt_in'].lower() == 'true'
        profile_api.update_email_opt_in(request.user, org, email_opt_in)
        return HttpResponse(status=status.HTTP_200_OK)
