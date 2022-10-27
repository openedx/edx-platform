"""Appsembler custom views for Studio

This module contains LoginView and support functions to enable local
login from Studio in MTE mode

See the LoginView class docstring for details on this class
"""

import logging
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import HttpResponseServerError
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views import View
from django.views.decorators.clickjacking import xframe_options_deny
from django.views.decorators.csrf import csrf_protect
from tahoe_sites.api import (
    deprecated_get_admin_users_queryset_by_email,
    get_organization_for_user,
    get_site_by_organization,
)

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_authn.utils import is_safe_login_or_logout_redirect
from student.roles import CourseCreatorRole, CourseInstructorRole, CourseStaffRole
from edxmako.shortcuts import render_to_response


logger = logging.getLogger(__name__)


def forgot_password_link():
    return "//{base}/login#forgot-password-modal".format(base=settings.LMS_BASE)


def platform_name():
    return configuration_helpers.get_value('platform_name',
                                           settings.PLATFORM_NAME)


def get_successful_login_next_url(request):
    """
    Return the successful login redirect URL.
    """
    next_url = request.GET.get('next')
    use_next_url = next_url and is_safe_login_or_logout_redirect(
        redirect_to=next_url,
        request_host=request.get_host(),
        dot_client_id=request.GET.get('client_id'),
        require_https=request.is_secure(),
    )

    if use_next_url:
        return next_url
    else:
        return reverse('home')


def render_login_page(login_error_message=None):
    """Convenience function to render the login page

    Arguments:
        login_error_message (str): error message to show. Doesn't show if None

    Returns:
        django.http.response.HttpResponse object with the login page content
    """
    return render_to_response(
        'login_page.html',
        {
            'login_error_message': login_error_message,
            'forgot_password_link': forgot_password_link(),
            'platform_name': platform_name(),
        }
    )


def find_global_admin_users(email):
    """Returns users matching the email who have global admin rights

    Checks for matches in the user model for the given email adderess and
    either staff or superuser rights (or both).
    Returns a User model queryset with zero or more records
    """
    return get_user_model().objects.filter(
        Q(is_staff=True) | Q(is_superuser=True),
        email=email
    )


def find_course_access_role_users(email):
    """Returns users matching the email who have specific course access roles

    The specific course access roles are those that allow the user to access
    Studio. These are:
    * CourseCreatorRole.ROLE
    * CourseInstructorRole.ROLE
    * CourseStaffRole.ROLE

    Returns a User model queryset with zero or more records
    """
    return get_user_model().objects.filter(
        email=email,
        courseaccessrole__role__in=[
            CourseCreatorRole.ROLE,
            CourseInstructorRole.ROLE,
            CourseStaffRole.ROLE,
        ])


def find_studio_authorized_users(email):
    """Returns users matching the email who can log into Studio
    This function is a convenience function that calls the following functions:
    * find_amc_admin_users
    * find_course_access_role_users

    The function combines the querset results of each and applies `.distinct()`
    in order to remove duplicates

    Returns a User model queryset with zero or more records
    """
    amc_admins = deprecated_get_admin_users_queryset_by_email(email)
    car_users = find_course_access_role_users(email)
    return (amc_admins | car_users).distinct()


class LoginView(View):
    """Basic login view class to allow for Studio local logins

    Allows a user account to log in to Studio using an email address and
    password under the following conditions:

    1. The email address is associated with only one user account
    2. The user account has a Studio authorized course access group role OR
       The user account has global staff or superuser privileges

    ## Tech Debt Note:

    Refactor this into a FormView class so we can shift the validation into a
    Form based class. Ideally we may be able to extend Django's `LoginView`
    and/or `AuthenticationForm` classes where we are replacing username with
    email for the form and using our authorization code

    By layering custom authorization on top of existing Django class based login
    code, we should be able to reduce the size of this class (less of our code)
    and rely on the platform more for security.
    """

    error_messages = {
        'invalid_login': _(
            'Email or password is incorrect. '
            'Please ensure that you are a course staff in order to use Studio.'
        ),
        'multiple_users_found': _(
            'We are unable to log you into Studio.'
            ' Please contact support@appsembler.com and quote the code'
            ' "studio-multiauth".'
        ),
    }

    @method_decorator(csrf_protect)
    @method_decorator(xframe_options_deny)
    def get(self, request):
        return render_login_page()

    @method_decorator(csrf_protect)
    def post(self, request):
        """Performs Studio local login for Tahoe

        This method tries to match users to the email address in the login
        form/page to identify a single authorized user to authorize and
        authenticate. It performs a priority check, first for global admin
        rights then for site specific rights

        If the email or password are missing from the post form data, then an
        `HttpResponseServerError` error is raised.

        If a single user match is found with global admin rights (the
        authorization step) then authentication with the password is performed.

        If a global admin user is not found, then this method checks for site
        admin rights and course access role rights. If a single user match is
        found (the authorization step) then authentication with the password
        is performed.

        If multiple authorized global admin matches are found, then an error
        message is returned matching the following entry in this class's error
        message dict:

        ```
        error_messages['multiple_users_found']
        ```

        If no gloabl admin users are found and multiple site admin and course
        access role authorized matches are found, then an error message is
        returned matching the following entry in this class's error message
        dict:

        ```
        error_messages['multiple_users_found']
        ```

        If no matches are found then an error message is returned to the login
        form/page matching the following entry in this class's error message
        dict:

        ```
        error_messages['invalid_login']
        ```

        If none of the above happen then an authentication attempt is made for
        the single found user with the password provided in the login form.

        If this passes, then the user is redirected to Studio's home page
        If the authentication fails, then the following entry in this class's
        error message dict:

        ```
        error_messages['invalid_login']
        ```
        """
        if 'email' not in request.POST or 'password' not in request.POST:
            # Expected fields in the post are missing
            logger.exception('Missing form data from Studio login form page')
            return HttpResponseServerError()

        email = self.request.POST['email']

        user = None

        global_admins = find_global_admin_users(email=email)
        if global_admins:
            if global_admins.count() > 1:
                self.log_multiple_objects_returned()
                return self.render_login_page_with_error('multiple_users_found')

            else:
                user = global_admins[0]

        if not user:
            studio_users = find_studio_authorized_users(email=email)
            if studio_users:
                if studio_users.count() > 1:
                    self.log_multiple_objects_returned()
                    return self.render_login_page_with_error('multiple_users_found')
                else:
                    user = studio_users[0]
            else:
                return self.render_login_page_with_error('invalid_login')

        if user:
            user = authenticate(self.request,
                                username=user.username,
                                password=self.request.POST['password'])
            if not user:
                return self.render_login_page_with_error('invalid_login')

            login(request, user)
            return redirect(get_successful_login_next_url(request))

    def log_multiple_objects_returned(self):
        if settings.FEATURES.get('SQUELCH_PII_IN_LOGS'):
            email = ''
        else:
            email = self.request.POST['email']

        logger.exception(
            'Studio Multi-Tenant Emails error: More than one user were '
            'found with the same email. '
            'Please change to a different email on either one of the '
            'accounts: {email}'.format(email=email)
        )

    def render_login_page_with_error(self, error_code):
        return render_login_page(
            login_error_message=self.error_messages[error_code])


def get_logout_redirect_url(request):
    """
    Return logout redirect url using the site related to the given user if possible.
    Otherwise, return settings.LOGOUT_REDIRECT_URL

    :return: logout redirect url or settings.LOGOUT_REDIRECT_URL
    """
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return reverse(settings.LOGOUT_REDIRECT_URL)

    try:
        organization = get_organization_for_user(user=user)
    except ObjectDoesNotExist:
        return reverse(settings.LOGOUT_REDIRECT_URL)
    site = get_site_by_organization(organization=organization)

    return '{protocol}://{site_domain}/logout'.format(
        protocol='https' if request.is_secure() else 'http',
        site_domain=site.domain
    )


class StudioLogoutView(View):
    """
    Studio Logout View
    """
    @method_decorator(csrf_protect)
    @method_decorator(login_required)
    def get(self, request):
        """
        Perform logout from studio, and redirect to LMS home page
        """
        return DjangoLogoutView.as_view(next_page=get_logout_redirect_url(request))(request)
