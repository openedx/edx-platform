""" Views for a student's account information. """
import base64
import json
import logging
import urlparse
from django.http import HttpResponseNotFound

import third_party_auth
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from edxmako.shortcuts import render_to_response, render_to_string
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from openedx.core.djangoapps.catalog.utils import get_programs_data
from student.helpers import get_next_url_for_login_page
from lms.djangoapps.courseware.views.views import add_tag_to_enrolled_courses
from student.views import (
    signin_user as old_login_view,
    register_user as old_register_view
)
from third_party_auth.decorators import xframe_allow_whitelisted
from util.cache import cache_if_anonymous
from util.enterprise_helpers import set_enterprise_branding_filter_param
from xmodule.modulestore.django import modulestore

from common.djangoapps.student.views import get_course_related_keys
from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.courseware.courses import get_courses, sort_by_start_date, get_course_by_id, sort_by_announcement
from lms.djangoapps.onboarding.helpers import reorder_registration_form_fields
from lms.djangoapps.student_account.views import _local_server_get, _get_form_descriptions, _external_auth_intercept, \
    _third_party_auth_context
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.theming.helpers import is_request_in_themed_site

AUDIT_LOG = logging.getLogger("audit")
log = logging.getLogger(__name__)
User = get_user_model()  # pylint:disable=invalid-name


def get_form_field_by_name(fields, name):
    """
    Get field object from list of form fields
    """
    for f in fields:
        if f['name'] == name:
            return f

    return None


@require_http_methods(['GET'])
@ensure_csrf_cookie
@xframe_allow_whitelisted
def login_and_registration_form(request, initial_mode="login", org_name=None, admin_email=None):
    """Render the combined login/registration form, defaulting to login

    This relies on the JS to asynchronously load the actual form from
    the user_api.

    Keyword Args:
        initial_mode (string): Either "login" or "register".

    """
    # Determine the URL to redirect to following login/registration/third_party_auth
    _local_server_get('/user_api/v1/account/registration/', request.session)
    redirect_to = get_next_url_for_login_page(request)
    # If we're already logged in, redirect to the dashboard
    if request.user.is_authenticated():
        return redirect(redirect_to)

    # Retrieve the form descriptions from the user API
    form_descriptions = _get_form_descriptions(request)

    # Our ?next= URL may itself contain a parameter 'tpa_hint=x' that we need to check.
    # If present, we display a login page focused on third-party auth with that provider.
    third_party_auth_hint = None
    if '?' in redirect_to:
        try:
            next_args = urlparse.parse_qs(urlparse.urlparse(redirect_to).query)
            provider_id = next_args['tpa_hint'][0]
            if third_party_auth.provider.Registry.get(provider_id=provider_id):
                third_party_auth_hint = provider_id
                initial_mode = "hinted_login"
        except (KeyError, ValueError, IndexError):
            pass

    set_enterprise_branding_filter_param(request=request, provider_id=third_party_auth_hint)

    # If this is a themed site, revert to the old login/registration pages.
    # We need to do this for now to support existing themes.
    # Themed sites can use the new logistration page by setting
    # 'ENABLE_COMBINED_LOGIN_REGISTRATION' in their
    # configuration settings.
    if is_request_in_themed_site() and not configuration_helpers.get_value('ENABLE_COMBINED_LOGIN_REGISTRATION', False):
        if initial_mode == "login":
            return old_login_view(request)
        elif initial_mode == "register":
            return old_register_view(request)

    # Allow external auth to intercept and handle the request
    ext_auth_response = _external_auth_intercept(request, initial_mode)
    if ext_auth_response is not None:
        return ext_auth_response

    # Otherwise, render the combined login/registration page
    context = {
        'data': {
            'login_redirect_url': redirect_to,
            'initial_mode': initial_mode,
            'third_party_auth': _third_party_auth_context(request, redirect_to),
            'third_party_auth_hint': third_party_auth_hint or '',
            'platform_name': configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME),
            'support_link': configuration_helpers.get_value('SUPPORT_SITE_LINK', settings.SUPPORT_SITE_LINK),

            # Include form descriptions retrieved from the user API.
            # We could have the JS client make these requests directly,
            # but we include them in the initial page load to avoid
            # the additional round-trip to the server.
            'login_form_desc': json.loads(form_descriptions['login']),
            'registration_form_desc': json.loads(form_descriptions['registration']),
            'password_reset_form_desc': json.loads(form_descriptions['password_reset']),
        },
        'login_redirect_url': redirect_to,  # This gets added to the query string of the "Sign In" button in header
        'responsive': True,
        'allow_iframing': True,
        'disable_courseware_js': True,
        'disable_footer': not configuration_helpers.get_value(
            'ENABLE_COMBINED_LOGIN_REGISTRATION_FOOTER',
            settings.FEATURES['ENABLE_COMBINED_LOGIN_REGISTRATION_FOOTER']
        ),
        'fields_to_disable': []
    }

    registration_fields = context['data']['registration_form_desc']['fields']
    registration_fields = context['data']['registration_form_desc']['fields'] = reorder_registration_form_fields(registration_fields)

    if org_name and admin_email:
        org_name = base64.b64decode(org_name)
        admin_email = base64.b64decode(admin_email)

        email_field = get_form_field_by_name(registration_fields, 'email')
        org_field = get_form_field_by_name(registration_fields, 'organization_name')
        is_poc_field = get_form_field_by_name(registration_fields, 'is_poc')
        email_field['defaultValue'] = admin_email
        org_field['defaultValue'] = org_name
        is_poc_field['defaultValue'] = "1"

        context['fields_to_disable'] = json.dumps([email_field['name'], org_field['name'], is_poc_field['name']])

    return render_to_response('student_account/login_and_register.html', context)

@ensure_csrf_cookie
@cache_if_anonymous()
def courses(request):
    """
    Render "find courses" page.  The course selection work is done in courseware.courses.
    """
    courses_list = []
    programs_list = []
    course_discovery_meanings = getattr(settings, 'COURSE_DISCOVERY_MEANINGS', {})
    if not settings.FEATURES.get('ENABLE_COURSE_DISCOVERY'):
        courses_list = get_courses(request.user)

        if configuration_helpers.get_value("ENABLE_COURSE_SORTING_BY_START_DATE",
                                           settings.FEATURES["ENABLE_COURSE_SORTING_BY_START_DATE"]):
            courses_list = sort_by_start_date(courses_list)
        else:
            courses_list = sort_by_announcement(courses_list)

    # Getting all the programs from course-catalog service. The programs_list is being added to the context but it's
    # not being used currently in courseware/courses.html. To use this list, you need to create a custom theme that
    # overrides courses.html. The modifications to courses.html to display the programs will be done after the support
    # for edx-pattern-library is added.
    if configuration_helpers.get_value("DISPLAY_PROGRAMS_ON_MARKETING_PAGES",
                                       settings.FEATURES.get("DISPLAY_PROGRAMS_ON_MARKETING_PAGES")):
        programs_list = get_programs_data(request.user)

    if request.user.is_authenticated():
        add_tag_to_enrolled_courses(request.user, courses_list)

    for course in  courses_list:
        course_key = SlashSeparatedCourseKey.from_deprecated_string(
                course.id.to_deprecated_string())
        with modulestore().bulk_operations(course_key):
            if has_access(request.user, 'load', course):
                first_chapter_url, first_section = get_course_related_keys(
                    request, get_course_by_id(course_key, 0))
                course_target = reverse('courseware_section', args=[
                    course.id.to_deprecated_string(),
                    first_chapter_url,
                    first_section
                    ])
                course.course_target = course_target
            else:
                course.course_target = '/courses/' + course.id.to_deprecated_string()

    return render_to_response(
        "courseware/courses.html",
        {
            'courses': courses_list,
            'course_discovery_meanings': course_discovery_meanings,
            'programs_list': programs_list
        }
    )


def render_404(request):
    try:
        return HttpResponseNotFound(render_to_string('custom_static_templates/404.html', {}, request=request))
    except:
        return redirect("404")