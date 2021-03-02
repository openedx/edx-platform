""" Views for a student's account information. """
import json
import logging
import urlparse
from datetime import datetime

import analytics
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import redirect
from django.template import TemplateDoesNotExist
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from eventtracking import tracker
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from pytz import utc
from ratelimitbackend.exceptions import RateLimitException
from w3lib.url import url_query_cleaner

import openedx.core.djangoapps.external_auth.views
from edxmako.shortcuts import marketing_link, render_to_response, render_to_string
from lms.djangoapps.courseware.access import _can_enroll_courselike, has_access
from lms.djangoapps.courseware.courses import get_course_by_id, get_courses, sort_by_announcement, sort_by_start_date
from lms.djangoapps.courseware.views.views import add_tag_to_enrolled_courses
from lms.djangoapps.onboarding.helpers import get_alquity_community_url
from lms.djangoapps.philu_api.helpers import get_course_custom_settings, get_social_sharing_urls
from lms.djangoapps.philu_overrides.constants import ENROLL_SHARE_DESC_FORMAT, ENROLL_SHARE_TITLE_FORMAT
from lms.djangoapps.philu_overrides.courseware.views.views import get_course_related_keys
from openedx.core.djangoapps.catalog.utils import get_programs_with_type  # pylint: disable=ungrouped-imports
from openedx.core.djangoapps.external_auth.models import ExternalAuthMap
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.theming.helpers import is_request_in_themed_site
from openedx.core.djangoapps.user_authn.cookies import set_logged_in_cookies
from openedx.core.djangoapps.user_authn.views.deprecated import register_user as old_register_view
from openedx.core.djangoapps.user_authn.views.deprecated import signin_user as old_login_view
from philu_overrides.helpers import (
    get_course_next_classes,
    get_next_url_for_login_page_override,
    get_user_current_enrolled_class,
    is_user_enrolled_in_any_class,
    reactivation_email_for_user_custom
)
from student.models import CourseEnrollment, LoginFailures
from third_party_auth import is_enabled as third_party_auth_enabled
from third_party_auth import pipeline, provider
from third_party_auth.decorators import xframe_allow_whitelisted
from util.cache import cache_if_anonymous
from util.json_request import JsonResponse
from xmodule.modulestore.django import modulestore

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
def login_and_registration_form(request, initial_mode="login"):
    """Render the combined login/registration form, defaulting to login

    This relies on the JS to asynchronously load the actual form from
    the user_api.

    Keyword Args:
        initial_mode (string): Either "login" or "register".

    """
    # Determine the URL to redirect to following login/registration/third_party_auth
    from openedx.core.djangoapps.user_authn.views.login_form import _external_auth_intercept, _get_form_descriptions,\
        _third_party_auth_context

    redirect_to = get_next_url_for_login_page_override(request)
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
            if provider.Registry.get(provider_id=provider_id):
                third_party_auth_hint = provider_id
                initial_mode = "hinted_login"
        except (KeyError, ValueError, IndexError):
            pass

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

    from util.philu_utils import extract_utm_params

    utm_params = extract_utm_params(request.GET)

    for utm_param, value in utm_params.items():
        request.session[utm_param] = value

    # Otherwise, render the combined login/registration page
    context = {
        'data': {
            'login_redirect_url': redirect_to,
            'initial_mode': initial_mode,
            'third_party_auth': _third_party_auth_context(request, redirect_to),
            'third_party_auth_hint': third_party_auth_hint or '',
            'platform_name': configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME),
            'support_link': configuration_helpers.get_value('SUPPORT_SITE_LINK', settings.SUPPORT_SITE_LINK),
            'password_reset_support_link':
                configuration_helpers.get_value('PASSWORD_RESET_SUPPORT_LINK', settings.SUPPORT_SITE_LINK),
            # Include form descriptions retrieved from the user API.
            # We could have the JS client make these requests directly,
            # but we include them in the initial page load to avoid
            # the additional round-trip to the server.
            'login_form_desc': json.loads(form_descriptions['login']),
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

    template = 'student_account/{}.html'.format(initial_mode)
    return render_to_response(template, context)


@ensure_csrf_cookie
@cache_if_anonymous()
def courses_custom(request):
    """
    Render "find courses" page.  The course selection work is done in courseware.courses.
    """
    from lms.djangoapps.courseware.views.views import get_last_accessed_courseware

    courses_list = []
    programs_list = []
    course_discovery_meanings = getattr(settings, 'COURSE_DISCOVERY_MEANINGS', {})
    if not settings.FEATURES.get('ENABLE_COURSE_DISCOVERY'):
        current_date = datetime.now(utc)
        courses_list = get_courses(request.user, filter_={'end__isnull': False}, exclude_={'end__lte': current_date})

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
        programs_list = get_programs_with_type(request.user)

    if request.user.is_authenticated():
        add_tag_to_enrolled_courses(request.user, courses_list)

    for course in courses_list:
        course_key = SlashSeparatedCourseKey.from_deprecated_string(
            course.id.to_deprecated_string())
        with modulestore().bulk_operations(course_key):
            if has_access(request.user, 'load', course):
                access_link = get_last_accessed_courseware(
                    get_course_by_id(course_key, 0),
                    request,
                    request.user
                )

                first_chapter_url, first_section = get_course_related_keys(
                    request, get_course_by_id(course_key, 0))
                first_target = reverse('courseware_section', args=[
                    course.id.to_deprecated_string(),
                    first_chapter_url,
                    first_section
                ])

                course.course_target = access_link or first_target
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


@ensure_csrf_cookie
@cache_if_anonymous()
def courses(request):
    """
    Render the "find courses" page. If the marketing site is enabled, redirect
    to that. Otherwise, if subdomain branding is on, this is the university
    profile page. Otherwise, it's the edX courseware.views.views.courses page
    """

    enable_mktg_site = configuration_helpers.get_value(
        'ENABLE_MKTG_SITE',
        settings.FEATURES.get('ENABLE_MKTG_SITE', False)
    )

    if enable_mktg_site:
        return redirect(marketing_link('COURSES'), permanent=True)

    if not settings.FEATURES.get('COURSES_ARE_BROWSABLE'):
        raise Http404

    #  we do not expect this case to be reached in cases where
    #  marketing is enabled or the courses are not browsable
    return courses_custom(request)


def render_404(request):
    try:
        return HttpResponseNotFound(render_to_string('custom_static_templates/404.html', {}, request=request))
    except TemplateDoesNotExist:
        return redirect("404/")


def render_500(request):
    try:
        render_server_error = render_to_string('custom_static_templates/server-error.html', {}, request=request)
        return HttpResponseServerError(render_server_error)
    except TemplateDoesNotExist:
        return redirect("500/")


# Need different levels of logging
@ensure_csrf_cookie
def login_user_custom(request, error=""):  # pylint: disable=too-many-statements,unused-argument
    """AJAX request to log in the user."""

    backend_name = None
    email = None
    password = None
    redirect_url = None
    response = None
    running_pipeline = None
    third_party_auth_requested = third_party_auth_enabled() and pipeline.running(request)
    third_party_auth_successful = False
    trumped_by_first_party_auth = bool(request.POST.get('email')) or bool(request.POST.get('password'))
    user = None
    platform_name = configuration_helpers.get_value("platform_name", settings.PLATFORM_NAME)

    if third_party_auth_requested and not trumped_by_first_party_auth:
        # The user has already authenticated via third-party auth and has not
        # asked to do first party auth by supplying a username or password. We
        # now want to put them through the same logging and cookie calculation
        # logic as with first-party auth.
        running_pipeline = pipeline.get(request)
        username = running_pipeline['kwargs'].get('username')
        backend_name = running_pipeline['backend']
        third_party_uid = running_pipeline['kwargs']['uid']
        requested_provider = provider.Registry.get_from_pipeline(running_pipeline)

        try:
            user = pipeline.get_authenticated_user(requested_provider, username, third_party_uid)
            third_party_auth_successful = True
        except User.DoesNotExist:
            AUDIT_LOG.warning(
                u"Login failed - user with username {username} has no social auth "
                "with backend_name {backend_name}".format(
                    username=username, backend_name=backend_name)
            )
            message = _(
                "You've successfully logged into your {provider_name} account, "
                "but this account isn't linked with an {platform_name} account yet."
            ).format(
                platform_name=platform_name,
                provider_name=requested_provider.name,
            )
            message += "<br/><br/>"
            message += _(
                "Use your {platform_name} username and password to log into {platform_name} below, "
                "and then link your {platform_name} account with {provider_name} from your dashboard."
            ).format(
                platform_name=platform_name,
                provider_name=requested_provider.name,
            )
            message += "<br/><br/>"
            message += _(
                "If you don't have an {platform_name} account yet, "
                "click <strong>Register</strong> at the top of the page."
            ).format(
                platform_name=platform_name
            )

            return HttpResponse(message, content_type="text/plain", status=403)

    else:

        if 'email' not in request.POST or 'password' not in request.POST:
            return JsonResponse({
                "success": False,
                # TODO: User error message
                "value": _('There was an error receiving your login information. Please email us.'),
            })  # TODO: this should be status code 400

        email = request.POST['email']
        password = request.POST['password']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            if settings.FEATURES['SQUELCH_PII_IN_LOGS']:
                AUDIT_LOG.warning(u"Login failed - Unknown user email")
            else:
                AUDIT_LOG.warning(u"Login failed - Unknown user email: {0}".format(email))

    # check if the user has a linked shibboleth account, if so, redirect the user to shib-login
    # This behavior is pretty much like what gmail does for shibboleth.  Try entering some @stanford.edu
    # address into the Gmail login.
    if settings.FEATURES.get('AUTH_USE_SHIB') and user:
        try:
            eamap = ExternalAuthMap.objects.get(user=user)
            if eamap.external_domain.startswith(openedx.core.djangoapps.external_auth.views.SHIBBOLETH_DOMAIN_PREFIX):
                return JsonResponse({
                    "success": False,
                    "redirect": reverse('shib-login'),
                })  # TODO: this should be status code 301  # pylint: disable=fixme
        except ExternalAuthMap.DoesNotExist:
            # This is actually the common case, logging in user without external linked login
            AUDIT_LOG.info(u"User %s w/o external auth attempting login", user)

    # see if account has been locked out due to excessive login failures
    user_found_by_email_lookup = user
    if user_found_by_email_lookup and LoginFailures.is_feature_enabled():
        if LoginFailures.is_user_locked_out(user_found_by_email_lookup):
            lockout_message = _('This account has been temporarily locked due '
                                'to excessive login failures. Try again later.')
            return JsonResponse({
                "success": False,
                "value": lockout_message,
            })  # TODO: this should be status code 429  # pylint: disable=fixme

    # if the user doesn't exist, we want to set the username to an invalid
    # username so that authentication is guaranteed to fail and we can take
    # advantage of the ratelimited backend
    username = user.username if user else ""

    if not third_party_auth_successful:
        try:
            user = authenticate(username=username, password=password, request=request)
        # this occurs when there are too many attempts from the same IP address
        except RateLimitException:
            return JsonResponse({
                "success": False,
                "value": _('Too many failed login attempts. Try again later.'),
            })  # TODO: this should be status code 429  # pylint: disable=fixme

    if user is None:
        # tick the failed login counters if the user exists in the database
        if user_found_by_email_lookup and LoginFailures.is_feature_enabled():
            LoginFailures.increment_lockout_counter(user_found_by_email_lookup)

        # if we didn't find this username earlier, the account for this email
        # doesn't exist, and doesn't have a corresponding password
        if username != "":
            if settings.FEATURES['SQUELCH_PII_IN_LOGS']:
                loggable_id = user_found_by_email_lookup.id if user_found_by_email_lookup else "<unknown>"
                AUDIT_LOG.warning(u"Login failed - password for user.id: {0} is invalid".format(loggable_id))
            else:
                AUDIT_LOG.warning(u"Login failed - password for {0} is invalid".format(email))
        return JsonResponse({
            "success": False,
            "value": _('Email or password is incorrect.'),
        })  # TODO: this should be status code 400  # pylint: disable=fixme

    # successful login, clear failed login attempts counters, if applicable
    if LoginFailures.is_feature_enabled():
        LoginFailures.clear_lockout_counter(user)

    # Track the user's sign in
    if hasattr(settings, 'LMS_SEGMENT_KEY') and settings.LMS_SEGMENT_KEY:
        tracking_context = tracker.get_tracker().resolve_context()
        analytics.identify(
            user.id,
            {
                'email': email,
                'username': username
            },
            {
                # Disable MailChimp because we don't want to update the user's email
                # and username in MailChimp on every page load. We only need to capture
                # this data on registration/activation.
                'MailChimp': False
            }
        )

        analytics.track(
            user.id,
            "edx.bi.user.account.authenticated",
            {
                'category': "conversion",
                'label': request.POST.get('course_id'),
                'provider': None
            },
            context={
                'ip': tracking_context.get('ip'),
                'Google Analytics': {
                    'clientId': tracking_context.get('client_id')
                }
            }
        )

    if user is not None and user.is_active:
        try:
            # We do not log here, because we have a handler registered
            # to perform logging on successful logins.
            login(request, user)
            if request.POST.get('remember') == 'true':
                request.session.set_expiry(604800)
                log.debug("Setting user session to never expire")
            else:
                request.session.set_expiry(0)
        except Exception as exc:
            AUDIT_LOG.critical("Login failed - Could not create session. Is memcached running?")
            log.critical("Login failed - Could not create session. Is memcached running?")
            log.exception(exc)
            raise

        redirect_url = None  # The AJAX method calling should know the default destination upon success
        if third_party_auth_successful:
            redirect_url = pipeline.get_complete_url(backend_name)

        response = JsonResponse({
            "success": True,
            "redirect_url": redirect_url,
        })

        # Ensure that the external marketing site can
        # detect that the user is logged in.
        return set_logged_in_cookies(request, response, user)

    if settings.FEATURES['SQUELCH_PII_IN_LOGS']:
        AUDIT_LOG.warning(u"Login failed - Account not active for user.id: {0}, resending activation".format(user.id))
    else:
        AUDIT_LOG.warning(u"Login failed - Account not active for user {0}, resending activation".format(username))

    reactivation_email_for_user_custom(request, user)
    not_activated_msg = _("Before you sign in, you need to activate your account. We have sent you an "
                          "email message with instructions for activating your account.")
    return JsonResponse({
        "success": False,
        "value": not_activated_msg,
    })  # TODO: this should be status code 400  # pylint: disable=fixme


@ensure_csrf_cookie
@cache_if_anonymous('share_after_enroll',)
def course_about(request, course_id):  # pylint: disable=too-many-statements
    """
    Display the course's about page.

    Assumes the course_id is in a valid format.
    """

    import urllib
    from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
    from util.milestones_helpers import get_prerequisite_courses_display
    from openedx.core.djangoapps.models.course_details import CourseDetails
    from commerce.utils import EcommerceService
    from course_modes.models import CourseMode, get_cosmetic_display_price
    from lms.djangoapps.courseware.access_utils import ACCESS_DENIED
    from lms.djangoapps.courseware.courses import get_studio_url
    from lms.envs.common import DEFAULT_IMAGE_NAME
    import shoppingcart
    from shoppingcart.utils import is_shopping_cart_enabled

    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    if hasattr(course_key, 'ccx'):
        # if un-enrolled/non-registered user try to access CCX (direct for registration)
        # then do not show him about page to avoid self registration.
        # Note: About page will only be shown to user who is not register. So that he can register. But for
        # CCX only CCX coach can enroll students.
        return redirect(reverse('dashboard'))

    with modulestore().bulk_operations(course_key):
        course = get_course_by_id(course_key)
        modes = CourseMode.modes_for_course_dict(course_key)

        if configuration_helpers.get_value('ENABLE_MKTG_SITE', settings.FEATURES.get('ENABLE_MKTG_SITE', False)):
            return redirect(reverse('info', args=[course.id.to_deprecated_string()]))

        staff_access = bool(has_access(request.user, 'staff', course))
        studio_url = get_studio_url(course, 'settings/details')

        if not staff_access and course.invitation_only and not CourseEnrollment.is_enrolled(request.user, course.id):
            raise Http404("Course not accessible: {}.".format(unicode(course.id)))

        # Note: this is a flow for payment for course registration, not the Verified Certificate flow.
        in_cart = False
        reg_then_add_to_cart_link = ""

        _is_shopping_cart_enabled = is_shopping_cart_enabled()
        if _is_shopping_cart_enabled:
            if request.user.is_authenticated():
                cart = shoppingcart.models.Order.get_cart_for_user(request.user)
                in_cart = shoppingcart.models.PaidCourseRegistration.contained_in_order(cart, course_key) or \
                    shoppingcart.models.CourseRegCodeItem.contained_in_order(cart, course_key)

            reg_then_add_to_cart_link = "{reg_url}?course_id={course_id}&enrollment_action=add_to_cart".format(
                reg_url=reverse('register_user'), course_id=urllib.quote(str(course_id))
            )

        # If the ecommerce checkout flow is enabled and the mode of the course is
        # professional or no id professional, we construct links for the enrollment
        # button to add the course to the ecommerce basket.
        ecomm_service = EcommerceService()
        ecommerce_checkout = ecomm_service.is_enabled(request.user)
        ecommerce_checkout_link = ''
        ecommerce_bulk_checkout_link = ''
        # professional_mode = None
        is_professional_mode = CourseMode.PROFESSIONAL in modes or CourseMode.NO_ID_PROFESSIONAL_MODE in modes
        if ecommerce_checkout and is_professional_mode:
            professional_mode = modes.get(CourseMode.PROFESSIONAL, '') or \
                modes.get(CourseMode.NO_ID_PROFESSIONAL_MODE, '')
            if professional_mode.sku:
                ecommerce_checkout_link = ecomm_service.get_checkout_page_url(professional_mode.sku)
            if professional_mode.bulk_sku:
                ecommerce_bulk_checkout_link = ecomm_service.get_checkout_page_url(professional_mode.bulk_sku)

        # Find the minimum price for the course across all course modes
        registration_price = CourseMode.min_course_price_for_currency(
            course_key,
            settings.PAID_COURSE_REGISTRATION_CURRENCY[0]
        )
        course_price = get_cosmetic_display_price(course)

        # Determine which checkout workflow to use -- LMS shoppingcart or Otto basket
        can_add_course_to_cart = _is_shopping_cart_enabled and registration_price and not ecommerce_checkout_link

        invitation_only = course.invitation_only

        # get prerequisite courses display names
        pre_requisite_courses = get_prerequisite_courses_display(course)

        # Overview
        overview = CourseOverview.get_from_id(course.id)

        course_next_classes = get_course_next_classes(request, course)
        current_class, user_current_enrolled_class, current_enrolled_class_target = get_user_current_enrolled_class(
            request, course)
        can_enroll = _can_enroll_courselike(request.user, current_class) if current_class else ACCESS_DENIED

        if current_class:
            if isinstance(current_class, CourseOverview):
                course_open_date = current_class.course_open_date
                current_class = get_course_by_id(current_class.id)
                current_class.course_open_date = course_open_date

            course_details = CourseDetails.populate(current_class)
        else:
            course_details = CourseDetails.populate(course)

        is_enrolled_in_any_class = is_user_enrolled_in_any_class(user_current_enrolled_class, course_next_classes)
        # Alquity specific check
        is_alquity = True if request.GET.get('ref') == 'alquity' else False

        custom_settings = get_course_custom_settings(course.id)
        meta_tags = custom_settings.get_course_meta_tags()

        meta_tags['description'] = meta_tags['description'] or course_details.short_description
        meta_tags['og:description'] = meta_tags['description']

        meta_tags['title'] = meta_tags['title'] or course_details.title or course.display_name
        meta_tags['og:title'] = meta_tags['title']
        meta_tags['addthis:title'] = ENROLL_SHARE_TITLE_FORMAT.format(course.display_name)

        if request.GET.get('share_after_enroll') == 'true':
            meta_tags['og:title'] = 'Join me in this free online course.'
            meta_tags['og:description'] = ENROLL_SHARE_DESC_FORMAT.format(course.display_name)

        if course_details.banner_image_name != DEFAULT_IMAGE_NAME:
            meta_tags['image'] = settings.LMS_ROOT_URL + course_details.banner_image_asset_path

        social_sharing_urls = get_social_sharing_urls(url_query_cleaner(request.build_absolute_uri()), meta_tags)

        is_mini_lesson = custom_settings.is_mini_lesson

        context = {
            'course': course,
            'course_details': course_details,
            'course_next_classes': course_next_classes,
            'current_class': current_class,
            'can_user_enroll': can_enroll.has_access,
            'user_current_enrolled_class': user_current_enrolled_class,
            'is_user_enrolled_in_any_class': is_enrolled_in_any_class,
            'current_enrolled_class_target': current_enrolled_class_target,
            'staff_access': staff_access,
            'studio_url': studio_url,
            'is_cosmetic_price_enabled': settings.FEATURES.get('ENABLE_COSMETIC_DISPLAY_PRICE'),
            'course_price': course_price,
            'reg_then_add_to_cart_link': reg_then_add_to_cart_link,
            'in_cart': in_cart,
            'ecommerce_bulk_checkout_link': ecommerce_bulk_checkout_link,
            'invitation_only': invitation_only,
            # We do not want to display the internal courseware header, which is used when the course is found in the
            # context. This value is therefor explicitly set to render the appropriate header.
            'disable_courseware_header': True,
            'can_add_course_to_cart': can_add_course_to_cart,
            'cart_link': reverse('shoppingcart.views.show_cart'),
            'pre_requisite_courses': pre_requisite_courses,
            'course_image_urls': overview.image_urls,
            'meta_tags': meta_tags,
            'is_alquity': is_alquity,
            'social_sharing_urls': social_sharing_urls,
            'is_mini_lesson': is_mini_lesson
        }

        return render_to_response('courseware/course_about.html', context)


def course_auto_enroll(request, course_id):
    """
    Auto enrolls any authenticated user in the course with course_id
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course_custom_settings = get_course_custom_settings(course_id)

    if request.user.is_anonymous():
        return redirect(get_alquity_community_url())

    if course_custom_settings.auto_enroll:
        CourseEnrollment.enroll(request.user, course_key)

    return redirect('/courses/{}/about?ref=alquity'.format(course_id))
