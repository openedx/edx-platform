"""
Helpers for edx student app
"""
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.http import int_to_base36

from openedx.adg.common.lib.mandrill_client.client import MandrillClient
from openedx.adg.common.lib.mandrill_client.tasks import task_send_mandrill_email
from openedx.adg.lms.helpers import get_user_first_name
from openedx.adg.lms.utils.env_utils import is_testing_environment
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangolib.markup import Text


def compose_and_send_adg_activation_email(user, activation_key):
    """
    Prepare and send email for account activation

    Arguments:
        user (User): Django user object
        activation_key (str): Activation key that will be sent as email content

    Returns:
        None
    """
    root_url = configuration_helpers.get_value('LMS_ROOT_URL', settings.LMS_ROOT_URL)
    activation_url = '{root_url}/activate/{activation_key}'.format(
        root_url=root_url,
        activation_key=activation_key
    )

    context = {
        'first_name': get_user_first_name(user),
        'activation_link': activation_url
    }

    task_send_mandrill_email(MandrillClient.USER_ACCOUNT_ACTIVATION, [user.email], context)


def compose_and_send_adg_password_reset_email(user, request):
    """
    Prepare and send email for password reset

    Arguments:
        user (User): Django user object
        request (Request): Request Object

    Returns:
        None
    """
    reset_link = '{protocol}://{site}{link}?track=pwreset'.format(
        protocol='https' if request.is_secure() else 'http',
        site=configuration_helpers.get_value('SITE_NAME', settings.SITE_NAME),
        link=reverse('password_reset_confirm', kwargs={
            'uidb36': int_to_base36(user.id),
            'token': default_token_generator.make_token(user),
        }),
    )

    context = {
        'first_name': get_user_first_name(user),
        'reset_link': reset_link
    }

    task_send_mandrill_email(MandrillClient.PASSWORD_RESET, [user.email], context)


def send_adg_password_reset_success_email(user, request):
    """
    Sends edx default email if the environment is testing. Otherwise, sends adg password reset
    success email
    """
    from openedx.core.djangoapps.user_authn.views.password_reset import send_password_reset_success_email

    if is_testing_environment():
        send_password_reset_success_email(user, request)
        return

    root_url = configuration_helpers.get_value('LMS_ROOT_URL', settings.LMS_ROOT_URL)
    context = {
        'first_name': get_user_first_name(user),
        'signin_link': '{}/login'.format(root_url),
    }

    task_send_mandrill_email(MandrillClient.PASSWORD_RESET_SUCCESS, [user.email], context)


def compose_and_send_adg_update_email_verification(new_email, use_https, confirm_link):
    """
    Prepare and send email for change email verification

    Arguments:
        new_email (str): Updated email address for user
        use_https (bool): Boolean to check if request is secure or not
        confirm_link (str): String containing confirmation link

    Returns:
        None
    """
    update_email_link = '{protocol}://{site}{link}'.format(
        protocol='https' if use_https else 'http',
        site=configuration_helpers.get_value('SITE_NAME', settings.SITE_NAME),
        link=confirm_link,
    )

    context = {
        'update_email_link': update_email_link
    }

    task_send_mandrill_email(MandrillClient.CHANGE_USER_EMAIL_ALERT, [new_email], context)


def compose_and_send_adg_update_email_confirmation(user, context):
    """
    Prepare and send email for change email confirmation

    Arguments:
        user (User): Django user object
        context (dict): Dictionary containing email content

    Returns:
        None
    """
    task_send_mandrill_email(MandrillClient.VERIFY_CHANGE_USER_EMAIL, [user.email], context)


def compose_and_send_adg_course_enrollment_confirmation_email(user, course_id):
    """
    Prepare and send email for enrollment confirmation

    Arguments:
        user (User): Django user object
        course_id (str): Id of course

    Returns:
        None
    """
    course = CourseOverview.objects.get(id=course_id)
    root_url = configuration_helpers.get_value('LMS_ROOT_URL', settings.LMS_ROOT_URL)
    course_url = '{root_url}/courses/{course_id}'.format(
        root_url=root_url,
        course_id=course.id
    )

    context = {
        'course_name': course.display_name,
        'course_url': course_url
    }
    task_send_mandrill_email.delay(MandrillClient.ENROLLMENT_CONFIRMATION, [user.email], context)


def compose_and_send_adg_course_enrollment_invitation_email(user_email, message_context):
    """
    Prepare and send email for enrollment invitation by instructor

    Arguments:
        user_email (str): Email address of user
        message_context (dict): Dictionary containing email content

    Returns:
        None
    """
    if 'display_name' in message_context:
        message_context['course_name'] = message_context['display_name']
    elif 'course' in message_context:
        message_context['course_name'] = Text(message_context['course'].display_name_with_default)

    user = User.objects.filter(email=user_email).select_related('profile').first()
    if user:
        message_context['full_name'] = user.profile.name

    message_context.pop('course')
    task_send_mandrill_email.delay(MandrillClient.COURSE_ENROLLMENT_INVITATION, [user_email], message_context)


def send_account_activation_email(user, profile, registration=None):
    """
    Send adg account activation emails.

    Args:
        user (User): User to which email will be sent.
        profile (UserProfile): Profile of the user.
        registration (Registration): Registration of the user.

    Returns:
        None
    """
    from common.djangoapps.student.views import compose_and_send_activation_email
    from common.djangoapps.student.models import Registration

    if is_testing_environment():
        compose_and_send_activation_email(user, profile, registration)
        return

    if registration is None:
        registration = Registration.objects.get(user=user)

    compose_and_send_adg_activation_email(user, registration.activation_key)
