"""Appsembler custom views for Studio

This module contains LoginView and support functions to enable local
login from Studio in MTE mode

See the LoginView class docstring for details on this class
"""

import logging
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login
from django.http import HttpResponseServerError
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views import View
from django.views.decorators.clickjacking import xframe_options_deny
from django.views.decorators.csrf import csrf_protect

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from student.models import CourseAccessRole
from student.roles import CourseCreatorRole, CourseInstructorRole, CourseStaffRole
from edxmako.shortcuts import render_to_response


logger = logging.getLogger(__name__)


def forgot_password_link():
    return "//{base}/login#forgot-password-modal".format(base=settings.LMS_BASE)


def platform_name():
    return configuration_helpers.get_value('platform_name',
                                           settings.PLATFORM_NAME)


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


def has_course_access_role(user):
    """Checks for account authorization to use Studio

    Arguments: user record for the account to check

    Returns:
        True if the account has a Studio authorized course access role
        False if the account does not have a Studio authorized course access
              role
    """
    return CourseAccessRole.objects.filter(
        user_id=user.id,
        role__in=[
            CourseCreatorRole.ROLE,
            CourseInstructorRole.ROLE,
            CourseStaffRole.ROLE,
        ]).exists()


def is_global_admin(user):
    """Checks for global authorization (is_staff or is_superuser)
    """
    return user.is_staff or user.is_superuser


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
    }

    @method_decorator(csrf_protect)
    @method_decorator(xframe_options_deny)
    def get(self, request):
        return render_login_page()

    @method_decorator(csrf_protect)
    def post(self, request):

        if 'email' not in request.POST or 'password' not in request.POST:
            # Expected fields in the post are missing
            logger.exception('Missing form data from Studio login form page')
            return HttpResponseServerError()

        user_model = get_user_model()
        try:
            user = user_model.objects.get(email=self.request.POST['email'])
            password = self.request.POST['password']

            user = authenticate(self.request,
                                username=user.username,
                                password=password)
            if not user:
                return self.render_login_page_with_error('invalid_login')
            # So we actually have a user at this point who has authenticated
            # Now see if the user has authorization
            if not (is_global_admin(user) or has_course_access_role(user)):
                return self.render_login_page_with_error('invalid_login')

            login(request, user)
            return redirect(reverse('home'))

        # Copy/paste/reformat from Tahoe Hawthorn common/student/views/login.py
        except user_model.MultipleObjectsReturned:
            self.log_multiple_objects_returned()
            # Raise the exception again.
            # Not very friendly but allows us to identify properly if enough
            # issues were reported instead of a silent error
            raise

        except user_model.DoesNotExist:
            return self.render_login_page_with_error('invalid_login')

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
