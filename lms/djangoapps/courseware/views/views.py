"""
Courseware views functions
"""

import json
import logging
import urllib
from collections import OrderedDict, namedtuple
from datetime import datetime

import analytics
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, AnonymousUser
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.core.context_processors import csrf
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.timezone import UTC
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.views.generic import View
from eventtracking import tracker
from ipware.ip import get_ip
from markupsafe import escape
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from rest_framework import status
from lms.djangoapps.instructor.views.api import require_global_staff

import shoppingcart
import survey.utils
import survey.views
from lms.djangoapps.ccx.utils import prep_course_for_grading
from certificates import api as certs_api
from certificates.models import CertificateStatuses
from openedx.core.djangoapps.models.course_details import CourseDetails
from commerce.utils import EcommerceService
from enrollment.api import add_enrollment
from course_modes.models import CourseMode
from lms.djangoapps.grades.new.course_grade import CourseGradeFactory
from courseware.access import has_access, has_ccx_coach_role, _adjust_start_date_for_beta_testers
from courseware.access_response import StartDateError
from courseware.access_utils import in_preview_mode
from courseware.courses import (
    get_courses,
    get_course,
    get_course_by_id,
    get_permission_for_course_about,
    get_studio_url,
    get_course_overview_with_access,
    get_course_with_access,
    sort_by_announcement,
    sort_by_start_date,
    UserNotEnrolled
)
from courseware.masquerade import setup_masquerade
from courseware.model_data import FieldDataCache
from courseware.models import StudentModule, BaseStudentModuleHistory
from courseware.url_helpers import get_redirect_url, get_redirect_url_for_global_staff
from courseware.user_state_client import DjangoXBlockUserStateClient
from edxmako.shortcuts import render_to_response, render_to_string, marketing_link
from lms.djangoapps.instructor.enrollment import uses_shib
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.coursetalk.helpers import inject_coursetalk_keys_into_context
from openedx.core.djangoapps.credit.api import (
    get_credit_requirement_status,
    is_user_eligible_for_credit,
    is_credit_course
)
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from shoppingcart.utils import is_shopping_cart_enabled
from openedx.core.djangoapps.self_paced.models import SelfPacedConfiguration
from student.models import UserTestGroup, CourseEnrollment
from student.roles import GlobalStaff
from util.cache import cache, cache_if_anonymous
from util.date_utils import strftime_localized
from util.db import outer_atomic
from util.milestones_helpers import get_prerequisite_courses_display
from util.views import _record_feedback_in_zendesk
from util.views import ensure_valid_course_key
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError, NoPathToItem
from xmodule.tabs import CourseTabList
from xmodule.x_module import STUDENT_VIEW
from lms.djangoapps.ccx.custom_exception import CCXLocatorValidationException
from ..entrance_exams import user_must_complete_entrance_exam
from ..module_render import get_module_for_descriptor, get_module, get_module_by_usage_id


log = logging.getLogger("edx.courseware")


# Only display the requirements on learner dashboard for
# credit and verified modes.
REQUIREMENTS_DISPLAY_MODES = CourseMode.CREDIT_MODES + [CourseMode.VERIFIED]

CertData = namedtuple("CertData", ["cert_status", "title", "msg", "download_url", "cert_web_view_url"])


def user_groups(user):
    """
    TODO (vshnayder): This is not used. When we have a new plan for groups, adjust appropriately.
    """
    if not user.is_authenticated():
        return []

    # TODO: Rewrite in Django
    key = 'user_group_names_{user.id}'.format(user=user)
    cache_expiration = 60 * 60  # one hour

    # Kill caching on dev machines -- we switch groups a lot
    group_names = cache.get(key)  # pylint: disable=no-member
    if settings.DEBUG:
        group_names = None

    if group_names is None:
        group_names = [u.name for u in UserTestGroup.objects.filter(users=user)]
        cache.set(key, group_names, cache_expiration)  # pylint: disable=no-member

    return group_names


@ensure_csrf_cookie
@cache_if_anonymous()
def courses(request):
    """
    Render "find courses" page.  The course selection work is done in courseware.courses.
    """
    courses_list = []
    course_discovery_meanings = getattr(settings, 'COURSE_DISCOVERY_MEANINGS', {})
    if not settings.FEATURES.get('ENABLE_COURSE_DISCOVERY'):
        courses_list = get_courses(request.user)

        if configuration_helpers.get_value(
                "ENABLE_COURSE_SORTING_BY_START_DATE",
                settings.FEATURES["ENABLE_COURSE_SORTING_BY_START_DATE"]
        ):
            courses_list = sort_by_start_date(courses_list)
        else:
            courses_list = sort_by_announcement(courses_list)

    return render_to_response(
        "courseware/courses.html",
        {'courses': courses_list, 'course_discovery_meanings': course_discovery_meanings}
    )


def get_current_child(xmodule, min_depth=None, requested_child=None):
    """
    Get the xmodule.position's display item of an xmodule that has a position and
    children.  If xmodule has no position or is out of bounds, return the first
    child with children of min_depth.

    For example, if chapter_one has no position set, with two child sections,
    section-A having no children and section-B having a discussion unit,
    `get_current_child(chapter, min_depth=1)`  will return section-B.

    Returns None only if there are no children at all.
    """
    def _get_child(children):
        """
        Returns either the first or last child based on the value of
        the requested_child parameter.  If requested_child is None,
        returns the first child.
        """
        if requested_child == 'first':
            return children[0]
        elif requested_child == 'last':
            return children[-1]
        else:
            return children[0]

    def _get_default_child_module(child_modules):
        """Returns the first child of xmodule, subject to min_depth."""
        if min_depth <= 0:
            return _get_child(child_modules)
        else:
            content_children = [
                child for child in child_modules
                if child.has_children_at_depth(min_depth - 1) and child.get_display_items()
            ]
            return _get_child(content_children) if content_children else None

    child = None
    if hasattr(xmodule, 'position'):
        children = xmodule.get_display_items()
        if len(children) > 0:
            if xmodule.position is not None and not requested_child:
                pos = xmodule.position - 1  # position is 1-indexed
                if 0 <= pos < len(children):
                    child = children[pos]
                    if min_depth > 0 and not child.has_children_at_depth(min_depth - 1):
                        child = None
            if child is None:
                child = _get_default_child_module(children)

    return child


@ensure_csrf_cookie
@ensure_valid_course_key
def jump_to_id(request, course_id, module_id):
    """
    This entry point allows for a shorter version of a jump to where just the id of the element is
    passed in. This assumes that id is unique within the course_id namespace
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    items = modulestore().get_items(course_key, qualifiers={'name': module_id})

    if len(items) == 0:
        raise Http404(
            u"Could not find id: {0} in course_id: {1}. Referer: {2}".format(
                module_id, course_id, request.META.get("HTTP_REFERER", "")
            ))
    if len(items) > 1:
        log.warning(
            u"Multiple items found with id: %s in course_id: %s. Referer: %s. Using first: %s",
            module_id,
            course_id,
            request.META.get("HTTP_REFERER", ""),
            items[0].location.to_deprecated_string()
        )

    return jump_to(request, course_id, items[0].location.to_deprecated_string())


@ensure_csrf_cookie
def jump_to(_request, course_id, location):
    """
    Show the page that contains a specific location.

    If the location is invalid or not in any class, return a 404.

    Otherwise, delegates to the index view to figure out whether this user
    has access, and what they should see.
    """
    try:
        course_key = CourseKey.from_string(course_id)
        usage_key = UsageKey.from_string(location).replace(course_key=course_key)
    except InvalidKeyError:
        raise Http404(u"Invalid course_key or usage_key")
    try:
        redirect_url = get_redirect_url(course_key, usage_key)
        user = _request.user
        user_is_global_staff = GlobalStaff().has_user(user)
        user_is_enrolled = CourseEnrollment.is_enrolled(user, course_key)
        if user_is_global_staff and not user_is_enrolled:
            redirect_url = get_redirect_url_for_global_staff(course_key, _next=redirect_url)
    except ItemNotFoundError:
        raise Http404(u"No data at this location: {0}".format(usage_key))
    except NoPathToItem:
        raise Http404(u"This location is not in any class: {0}".format(usage_key))

    return redirect(redirect_url)


@ensure_csrf_cookie
@ensure_valid_course_key
def course_info(request, course_id):
    """
    Display the course's info.html, or 404 if there is no such course.

    Assumes the course_id is in a valid format.
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    with modulestore().bulk_operations(course_key):
        course = get_course_by_id(course_key, depth=2)
        access_response = has_access(request.user, 'load', course, course_key)

        if not access_response:

            # The user doesn't have access to the course. If they're
            # denied permission due to the course not being live yet,
            # redirect to the dashboard page.
            if isinstance(access_response, StartDateError):
                start_date = strftime_localized(course.start, 'SHORT_DATE')
                params = urllib.urlencode({'notlive': start_date})
                return redirect('{0}?{1}'.format(reverse('dashboard'), params))
            # Otherwise, give a 404 to avoid leaking info about access
            # control.
            raise Http404("Course not found.")

        staff_access = has_access(request.user, 'staff', course)
        masquerade, user = setup_masquerade(request, course_key, staff_access, reset_masquerade_data=True)

        # if user is not enrolled in a course then app will show enroll/get register link inside course info page.
        show_enroll_banner = request.user.is_authenticated() and not CourseEnrollment.is_enrolled(user, course.id)
        if show_enroll_banner and hasattr(course_key, 'ccx'):
            # if course is CCX and user is not enrolled/registered then do not let him open course direct via link for
            # self registration. Because only CCX coach can register/enroll a student. If un-enrolled user try
            # to access CCX redirect him to dashboard.
            return redirect(reverse('dashboard'))

        # If the user needs to take an entrance exam to access this course, then we'll need
        # to send them to that specific course module before allowing them into other areas
        if user_must_complete_entrance_exam(request, user, course):
            return redirect(reverse('courseware', args=[unicode(course.id)]))

        # check to see if there is a required survey that must be taken before
        # the user can access the course.
        if request.user.is_authenticated() and survey.utils.must_answer_survey(course, user):
            return redirect(reverse('course_survey', args=[unicode(course.id)]))

        is_from_dashboard = reverse('dashboard') in request.META.get('HTTP_REFERER', [])
        if course.bypass_home and is_from_dashboard:
            return redirect(reverse('courseware', args=[course_id]))

        studio_url = get_studio_url(course, 'course_info')

        # link to where the student should go to enroll in the course:
        # about page if there is not marketing site, SITE_NAME if there is
        url_to_enroll = reverse(course_about, args=[course_id])
        if settings.FEATURES.get('ENABLE_MKTG_SITE'):
            url_to_enroll = marketing_link('COURSES')

        context = {
            'request': request,
            'masquerade_user': user,
            'course_id': course_key.to_deprecated_string(),
            'cache': None,
            'course': course,
            'staff_access': staff_access,
            'masquerade': masquerade,
            'studio_url': studio_url,
            'show_enroll_banner': show_enroll_banner,
            'url_to_enroll': url_to_enroll,
        }

        # Get the URL of the user's last position in order to display the 'where you were last' message
        context['last_accessed_courseware_url'] = None
        if SelfPacedConfiguration.current().enable_course_home_improvements:
            context['last_accessed_courseware_url'] = get_last_accessed_courseware(course, request, user)

        now = datetime.now(UTC())
        effective_start = _adjust_start_date_for_beta_testers(user, course, course_key)
        if not in_preview_mode() and staff_access and now < effective_start:
            # Disable student view button if user is staff and
            # course is not yet visible to students.
            context['disable_student_access'] = True

        if CourseEnrollment.is_enrolled(request.user, course.id):
            inject_coursetalk_keys_into_context(context, course_key)

        return render_to_response('courseware/info.html', context)


def get_last_accessed_courseware(course, request, user):
    """
    Return the courseware module URL that the user last accessed,
    or None if it cannot be found.
    """
    field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
        course.id, request.user, course, depth=2
    )
    course_module = get_module_for_descriptor(
        user, request, course, field_data_cache, course.id, course=course
    )
    chapter_module = get_current_child(course_module)
    if chapter_module is not None:
        section_module = get_current_child(chapter_module)
        if section_module is not None:
            url = reverse('courseware_section', kwargs={
                'course_id': unicode(course.id),
                'chapter': chapter_module.url_name,
                'section': section_module.url_name
            })
            return url
    return None


@ensure_csrf_cookie
@ensure_valid_course_key
def static_tab(request, course_id, tab_slug):
    """
    Display the courses tab with the given name.

    Assumes the course_id is in a valid format.
    """

    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    course = get_course_with_access(request.user, 'load', course_key)

    tab = CourseTabList.get_tab_by_slug(course.tabs, tab_slug)
    if tab is None:
        raise Http404

    contents = get_static_tab_contents(
        request,
        course,
        tab
    )
    if contents is None:
        raise Http404

    return render_to_response('courseware/static_tab.html', {
        'course': course,
        'tab': tab,
        'tab_contents': contents,
    })


@ensure_csrf_cookie
@ensure_valid_course_key
def syllabus(request, course_id):
    """
    Display the course's syllabus.html, or 404 if there is no such course.

    Assumes the course_id is in a valid format.
    """

    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    course = get_course_with_access(request.user, 'load', course_key)
    staff_access = bool(has_access(request.user, 'staff', course))

    return render_to_response('courseware/syllabus.html', {
        'course': course,
        'staff_access': staff_access,
    })


def registered_for_course(course, user):
    """
    Return True if user is registered for course, else False
    """
    if user is None:
        return False
    if user.is_authenticated():
        return CourseEnrollment.is_enrolled(user, course.id)
    else:
        return False


def get_cosmetic_display_price(course, registration_price):
    """
    Return Course Price as a string preceded by correct currency, or 'Free'
    """
    currency_symbol = settings.PAID_COURSE_REGISTRATION_CURRENCY[1]

    price = course.cosmetic_display_price
    if registration_price > 0:
        price = registration_price

    if price:
        # Translators: This will look like '$50', where {currency_symbol} is a symbol such as '$' and {price} is a
        # numerical amount in that currency. Adjust this display as needed for your language.
        return _("{currency_symbol}{price}").format(currency_symbol=currency_symbol, price=price)
    else:
        # Translators: This refers to the cost of the course. In this case, the course costs nothing so it is free.
        return _('Free')


class EnrollStaffView(View):
    """
    Displays view for registering in the course to a global staff user.

    User can either choose to 'Enroll' or 'Don't Enroll' in the course.
      Enroll: Enrolls user in course and redirects to the courseware.
      Don't Enroll: Redirects user to course about page.

    Arguments:
     - request    : HTTP request
     - course_id  : course id

    Returns:
     - RedirectResponse
    """
    template_name = 'enroll_staff.html'

    @method_decorator(require_global_staff)
    @method_decorator(ensure_valid_course_key)
    def get(self, request, course_id):
        """
        Display enroll staff view to global staff user with `Enroll` and `Don't Enroll` options.
        """
        user = request.user
        course_key = CourseKey.from_string(course_id)
        with modulestore().bulk_operations(course_key):
            course = get_course_with_access(user, 'load', course_key)
            if not registered_for_course(course, user):
                context = {
                    'course': course,
                    'csrftoken': csrf(request)["csrf_token"]
                }
                return render_to_response(self.template_name, context)

    @method_decorator(require_global_staff)
    @method_decorator(ensure_valid_course_key)
    def post(self, request, course_id):
        """
        Either enrolls the user in course or redirects user to course about page
        depending upon the option (Enroll, Don't Enroll) chosen by the user.
        """
        _next = urllib.quote_plus(request.GET.get('next', 'info'), safe='/:?=')
        course_key = CourseKey.from_string(course_id)
        enroll = 'enroll' in request.POST
        if enroll:
            add_enrollment(request.user.username, course_id)
            log.info(
                u"User %s enrolled in %s via `enroll_staff` view",
                request.user.username,
                course_id
            )
            return redirect(_next)

        # In any other case redirect to the course about page.
        return redirect(reverse('about_course', args=[unicode(course_key)]))


@ensure_csrf_cookie
@cache_if_anonymous()
def course_about(request, course_id):
    """
    Display the course's about page.

    Assumes the course_id is in a valid format.
    """

    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    if hasattr(course_key, 'ccx'):
        # if un-enrolled/non-registered user try to access CCX (direct for registration)
        # then do not show him about page to avoid self registration.
        # Note: About page will only be shown to user who is not register. So that he can register. But for
        # CCX only CCX coach can enroll students.
        return redirect(reverse('dashboard'))

    with modulestore().bulk_operations(course_key):
        permission = get_permission_for_course_about()
        course = get_course_with_access(request.user, permission, course_key)
        course_details = CourseDetails.populate(course)
        modes = CourseMode.modes_for_course_dict(course_key)

        if configuration_helpers.get_value('ENABLE_MKTG_SITE', settings.FEATURES.get('ENABLE_MKTG_SITE', False)):
            return redirect(reverse('info', args=[course.id.to_deprecated_string()]))

        registered = registered_for_course(course, request.user)

        staff_access = bool(has_access(request.user, 'staff', course))
        studio_url = get_studio_url(course, 'settings/details')

        if has_access(request.user, 'load', course):
            course_target = reverse('info', args=[course.id.to_deprecated_string()])
        else:
            course_target = reverse('about_course', args=[course.id.to_deprecated_string()])

        show_courseware_link = bool(
            (
                has_access(request.user, 'load', course) and
                has_access(request.user, 'view_courseware_with_prerequisites', course)
            ) or settings.FEATURES.get('ENABLE_LMS_MIGRATION')
        )

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
        professional_mode = None
        is_professional_mode = CourseMode.PROFESSIONAL in modes or CourseMode.NO_ID_PROFESSIONAL_MODE in modes
        if ecommerce_checkout and is_professional_mode:
            professional_mode = modes.get(CourseMode.PROFESSIONAL, '') or \
                modes.get(CourseMode.NO_ID_PROFESSIONAL_MODE, '')
            if professional_mode.sku:
                ecommerce_checkout_link = ecomm_service.checkout_page_url(professional_mode.sku)
            if professional_mode.bulk_sku:
                ecommerce_bulk_checkout_link = ecomm_service.checkout_page_url(professional_mode.bulk_sku)

        # Find the minimum price for the course across all course modes
        registration_price = CourseMode.min_course_price_for_currency(
            course_key,
            settings.PAID_COURSE_REGISTRATION_CURRENCY[0]
        )
        course_price = get_cosmetic_display_price(course, registration_price)

        # Determine which checkout workflow to use -- LMS shoppingcart or Otto basket
        can_add_course_to_cart = _is_shopping_cart_enabled and registration_price and not ecommerce_checkout_link

        # Used to provide context to message to student if enrollment not allowed
        can_enroll = bool(has_access(request.user, 'enroll', course))
        invitation_only = course.invitation_only
        is_course_full = CourseEnrollment.objects.is_course_full(course)

        # Register button should be disabled if one of the following is true:
        # - Student is already registered for course
        # - Course is already full
        # - Student cannot enroll in course
        active_reg_button = not(registered or is_course_full or not can_enroll)

        is_shib_course = uses_shib(course)

        # get prerequisite courses display names
        pre_requisite_courses = get_prerequisite_courses_display(course)

        # Overview
        overview = CourseOverview.get_from_id(course.id)

        context = {
            'course': course,
            'course_details': course_details,
            'staff_access': staff_access,
            'studio_url': studio_url,
            'registered': registered,
            'course_target': course_target,
            'is_cosmetic_price_enabled': settings.FEATURES.get('ENABLE_COSMETIC_DISPLAY_PRICE'),
            'course_price': course_price,
            'in_cart': in_cart,
            'ecommerce_checkout': ecommerce_checkout,
            'ecommerce_checkout_link': ecommerce_checkout_link,
            'ecommerce_bulk_checkout_link': ecommerce_bulk_checkout_link,
            'professional_mode': professional_mode,
            'reg_then_add_to_cart_link': reg_then_add_to_cart_link,
            'show_courseware_link': show_courseware_link,
            'is_course_full': is_course_full,
            'can_enroll': can_enroll,
            'invitation_only': invitation_only,
            'active_reg_button': active_reg_button,
            'is_shib_course': is_shib_course,
            # We do not want to display the internal courseware header, which is used when the course is found in the
            # context. This value is therefor explicitly set to render the appropriate header.
            'disable_courseware_header': True,
            'can_add_course_to_cart': can_add_course_to_cart,
            'cart_link': reverse('shoppingcart.views.show_cart'),
            'pre_requisite_courses': pre_requisite_courses,
            'course_image_urls': overview.image_urls,
        }
        inject_coursetalk_keys_into_context(context, course_key)

        return render_to_response('courseware/course_about.html', context)


@transaction.non_atomic_requests
@login_required
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@ensure_valid_course_key
def progress(request, course_id, student_id=None):
    """ Display the progress page. """
    course_key = CourseKey.from_string(course_id)

    with modulestore().bulk_operations(course_key):
        return _progress(request, course_key, student_id)


def _progress(request, course_key, student_id):
    """
    Unwrapped version of "progress".

    User progress. We show the grade bar and every problem score.

    Course staff are allowed to see the progress of students in their class.
    """

    if student_id is not None:
        try:
            student_id = int(student_id)
        # Check for ValueError if 'student_id' cannot be converted to integer.
        except ValueError:
            raise Http404

    course = get_course_with_access(request.user, 'load', course_key, depth=None, check_if_enrolled=True)
    prep_course_for_grading(course, request)

    # check to see if there is a required survey that must be taken before
    # the user can access the course.
    if survey.utils.must_answer_survey(course, request.user):
        return redirect(reverse('course_survey', args=[unicode(course.id)]))

    staff_access = bool(has_access(request.user, 'staff', course))

    if student_id is None or student_id == request.user.id:
        # always allowed to see your own profile
        student = request.user
    else:
        try:
            coach_access = has_ccx_coach_role(request.user, course_key)
        except CCXLocatorValidationException:
            coach_access = False

        has_access_on_students_profiles = staff_access or coach_access
        # Requesting access to a different student's profile
        if not has_access_on_students_profiles:
            raise Http404
        try:
            student = User.objects.get(id=student_id)
        except User.DoesNotExist:
            raise Http404

    # NOTE: To make sure impersonation by instructor works, use
    # student instead of request.user in the rest of the function.

    # The pre-fetching of groups is done to make auth checks not require an
    # additional DB lookup (this kills the Progress page in particular).
    student = User.objects.prefetch_related("groups").get(id=student.id)

    course_grade = CourseGradeFactory(student).create(course)
    if not course_grade.has_access_to_course:
        # This means the student didn't have access to the course (which the instructor requested)
        raise Http404

    courseware_summary = course_grade.chapter_grades
    grade_summary = course_grade.summary

    studio_url = get_studio_url(course, 'settings/grading')

    # checking certificate generation configuration
    enrollment_mode, is_active = CourseEnrollment.enrollment_mode_for_user(student, course_key)

    context = {
        'course': course,
        'courseware_summary': courseware_summary,
        'studio_url': studio_url,
        'grade_summary': grade_summary,
        'staff_access': staff_access,
        'student': student,
        'passed': is_course_passed(course, grade_summary),
        'credit_course_requirements': _credit_course_requirements(course_key, student),
        'certificate_data': _get_cert_data(student, course, course_key, is_active, enrollment_mode)
    }

    with outer_atomic():
        response = render_to_response('courseware/progress.html', context)

    return response


def _get_cert_data(student, course, course_key, is_active, enrollment_mode):
    """Returns students course certificate related data.

    Arguments:
        student (User): Student for whom certificate to retrieve.
        course (Course): Course object for which certificate data to retrieve.
        course_key (CourseKey): Course identifier for course.
        is_active (Bool): Boolean value to check if course is active.
        enrollment_mode (String): Course mode in which student is enrolled.

    Returns:
        returns dict if course certificate is available else None.
    """

    if enrollment_mode == CourseMode.AUDIT:
        return CertData(
            CertificateStatuses.audit_passing,
            _('Your enrollment: Audit track'),
            _('You are enrolled in the audit track for this course. The audit track does not include a certificate.'),
            download_url=None,
            cert_web_view_url=None
        )

    show_generate_cert_btn = (
        is_active and CourseMode.is_eligible_for_certificate(enrollment_mode)
        and certs_api.cert_generation_enabled(course_key)
    )

    if not show_generate_cert_btn:
        return None

    if certs_api.is_certificate_invalid(student, course_key):
        return CertData(
            CertificateStatuses.invalidated,
            _('Your certificate has been invalidated'),
            _('Please contact your course team if you have any questions.'),
            download_url=None,
            cert_web_view_url=None
        )

    cert_downloadable_status = certs_api.certificate_downloadable_status(student, course_key)

    if cert_downloadable_status['is_downloadable']:
        cert_status = CertificateStatuses.downloadable
        title = _('Your certificate is available')
        msg = _('You can keep working for a higher grade, or request your certificate now.')
        if certs_api.has_html_certificates_enabled(course_key, course):
            if certs_api.get_active_web_certificate(course) is not None:
                cert_web_view_url = certs_api.get_certificate_url(
                    course_id=course_key, uuid=cert_downloadable_status['uuid']
                )
                return CertData(cert_status, title, msg, download_url=None, cert_web_view_url=cert_web_view_url)
            else:
                return CertData(
                    CertificateStatuses.generating,
                    _("We're working on it..."),
                    _(
                        "We're creating your certificate. You can keep working in your courses and a link "
                        "to it will appear here and on your Dashboard when it is ready."
                    ),
                    download_url=None,
                    cert_web_view_url=None
                )

        return CertData(
            cert_status, title, msg, download_url=cert_downloadable_status['download_url'], cert_web_view_url=None
        )

    if cert_downloadable_status['is_generating']:
        return CertData(
            CertificateStatuses.generating,
            _("We're working on it..."),
            _(
                "We're creating your certificate. You can keep working in your courses and a link to "
                "it will appear here and on your Dashboard when it is ready."
            ),
            download_url=None,
            cert_web_view_url=None
        )

    # If the learner is in verified modes and the student did not have
    # their ID verified, we need to show message to ask learner to verify their ID first
    missing_required_verification = enrollment_mode in CourseMode.VERIFIED_MODES and \
        not SoftwareSecurePhotoVerification.user_is_verified(student)

    if missing_required_verification or cert_downloadable_status['is_unverified']:
        platform_name = configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME)
        return CertData(
            CertificateStatuses.unverified,
            _('Certificate unavailable'),
            _(
                'You have not received a certificate because you do not have a current {platform_name} '
                'verified identity.'
            ).format(platform_name=platform_name),
            download_url=None,
            cert_web_view_url=None
        )

    return CertData(
        CertificateStatuses.requesting,
        _('Congratulations, you qualified for a certificate!'),
        _('You can keep working for a higher grade, or request your certificate now.'),
        download_url=None,
        cert_web_view_url=None
    )


def _credit_course_requirements(course_key, student):
    """Return information about which credit requirements a user has satisfied.

    Arguments:
        course_key (CourseKey): Identifier for the course.
        student (User): Currently logged in user.

    Returns: dict if the credit eligibility enabled and it is a credit course
    and the user is enrolled in either verified or credit mode, and None otherwise.

    """
    # If credit eligibility is not enabled or this is not a credit course,
    # short-circuit and return `None`.  This indicates that credit requirements
    # should NOT be displayed on the progress page.
    if not (settings.FEATURES.get("ENABLE_CREDIT_ELIGIBILITY", False) and is_credit_course(course_key)):
        return None

    # This indicates that credit requirements should NOT be displayed on the progress page.
    enrollment = CourseEnrollment.get_enrollment(student, course_key)
    if enrollment and enrollment.mode not in REQUIREMENTS_DISPLAY_MODES:
        return None

    # Credit requirement statuses for which user does not remain eligible to get credit.
    non_eligible_statuses = ['failed', 'declined']

    # Retrieve the status of the user for each eligibility requirement in the course.
    # For each requirement, the user's status is either "satisfied", "failed", or None.
    # In this context, `None` means that we don't know the user's status, either because
    # the user hasn't done something (for example, submitting photos for verification)
    # or we're waiting on more information (for example, a response from the photo
    # verification service).
    requirement_statuses = get_credit_requirement_status(course_key, student.username)

    # If the user has been marked as "eligible", then they are *always* eligible
    # unless someone manually intervenes.  This could lead to some strange behavior
    # if the requirements change post-launch.  For example, if the user was marked as eligible
    # for credit, then a new requirement was added, the user will see that they're eligible
    # AND that one of the requirements is still pending.
    # We're assuming here that (a) we can mitigate this by properly training course teams,
    # and (b) it's a better user experience to allow students who were at one time
    # marked as eligible to continue to be eligible.
    # If we need to, we can always manually move students back to ineligible by
    # deleting CreditEligibility records in the database.
    if is_user_eligible_for_credit(student.username, course_key):
        eligibility_status = "eligible"

    # If the user has *failed* any requirements (for example, if a photo verification is denied),
    # then the user is NOT eligible for credit.
    elif any(requirement['status'] in non_eligible_statuses for requirement in requirement_statuses):
        eligibility_status = "not_eligible"

    # Otherwise, the user may be eligible for credit, but the user has not
    # yet completed all the requirements.
    else:
        eligibility_status = "partial_eligible"

    return {
        'eligibility_status': eligibility_status,
        'requirements': requirement_statuses,
    }


@login_required
@ensure_valid_course_key
def submission_history(request, course_id, student_username, location):
    """Render an HTML fragment (meant for inclusion elsewhere) that renders a
    history of all state changes made by this user for this problem location.
    Right now this only works for problems because that's all
    StudentModuleHistory records.
    """

    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    try:
        usage_key = course_key.make_usage_key_from_deprecated_string(location)
    except (InvalidKeyError, AssertionError):
        return HttpResponse(escape(_(u'Invalid location.')))

    course = get_course_overview_with_access(request.user, 'load', course_key)
    staff_access = bool(has_access(request.user, 'staff', course))

    # Permission Denied if they don't have staff access and are trying to see
    # somebody else's submission history.
    if (student_username != request.user.username) and (not staff_access):
        raise PermissionDenied

    user_state_client = DjangoXBlockUserStateClient()
    try:
        history_entries = list(user_state_client.get_history(student_username, usage_key))
    except DjangoXBlockUserStateClient.DoesNotExist:
        return HttpResponse(escape(_(u'User {username} has never accessed problem {location}').format(
            username=student_username,
            location=location
        )))

    # This is ugly, but until we have a proper submissions API that we can use to provide
    # the scores instead, it will have to do.
    csm = StudentModule.objects.filter(
        module_state_key=usage_key,
        student__username=student_username,
        course_id=course_key)

    scores = BaseStudentModuleHistory.get_history(csm)

    if len(scores) != len(history_entries):
        log.warning(
            "Mismatch when fetching scores for student "
            "history for course %s, user %s, xblock %s. "
            "%d scores were found, and %d history entries were found. "
            "Matching scores to history entries by date for display.",
            course_id,
            student_username,
            location,
            len(scores),
            len(history_entries),
        )
        scores_by_date = {
            score.created: score
            for score in scores
        }
        scores = [
            scores_by_date[history.updated]
            for history in history_entries
        ]

    context = {
        'history_entries': history_entries,
        'scores': scores,
        'username': student_username,
        'location': location,
        'course_id': course_key.to_deprecated_string()
    }

    return render_to_response('courseware/submission_history.html', context)


def get_static_tab_contents(request, course, tab):
    """
    Returns the contents for the given static tab
    """
    loc = course.id.make_usage_key(
        tab.type,
        tab.url_slug,
    )
    field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
        course.id, request.user, modulestore().get_item(loc), depth=0
    )
    tab_module = get_module(
        request.user, request, loc, field_data_cache, static_asset_path=course.static_asset_path, course=course
    )

    logging.debug('course_module = %s', tab_module)

    html = ''
    if tab_module is not None:
        try:
            html = tab_module.render(STUDENT_VIEW).content
        except Exception:  # pylint: disable=broad-except
            html = render_to_string('courseware/error-message.html', None)
            log.exception(
                u"Error rendering course=%s, tab=%s", course, tab['url_slug']
            )

    return html


@require_GET
@ensure_valid_course_key
def get_course_lti_endpoints(request, course_id):
    """
    View that, given a course_id, returns the a JSON object that enumerates all of the LTI endpoints for that course.

    The LTI 2.0 result service spec at
    http://www.imsglobal.org/lti/ltiv2p0/uml/purl.imsglobal.org/vocab/lis/v2/outcomes/Result/service.html
    says "This specification document does not prescribe a method for discovering the endpoint URLs."  This view
    function implements one way of discovering these endpoints, returning a JSON array when accessed.

    Arguments:
        request (django request object):  the HTTP request object that triggered this view function
        course_id (unicode):  id associated with the course

    Returns:
        (django response object):  HTTP response.  404 if course is not found, otherwise 200 with JSON body.
    """

    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    try:
        course = get_course(course_key, depth=2)
    except ValueError:
        return HttpResponse(status=404)

    anonymous_user = AnonymousUser()
    anonymous_user.known = False  # make these "noauth" requests like module_render.handle_xblock_callback_noauth
    lti_descriptors = modulestore().get_items(course.id, qualifiers={'category': 'lti'})

    lti_noauth_modules = [
        get_module_for_descriptor(
            anonymous_user,
            request,
            descriptor,
            FieldDataCache.cache_for_descriptor_descendents(
                course_key,
                anonymous_user,
                descriptor
            ),
            course_key,
            course=course
        )
        for descriptor in lti_descriptors
    ]

    endpoints = [
        {
            'display_name': module.display_name,
            'lti_2_0_result_service_json_endpoint': module.get_outcome_service_url(
                service_name='lti_2_0_result_rest_handler') + "/user/{anon_user_id}",
            'lti_1_1_result_service_xml_endpoint': module.get_outcome_service_url(
                service_name='grade_handler'),
        }
        for module in lti_noauth_modules
    ]

    return HttpResponse(json.dumps(endpoints), content_type='application/json')


@login_required
def course_survey(request, course_id):
    """
    URL endpoint to present a survey that is associated with a course_id
    Note that the actual implementation of course survey is handled in the
    views.py file in the Survey Djangoapp
    """

    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = get_course_with_access(request.user, 'load', course_key)

    redirect_url = reverse('info', args=[course_id])

    # if there is no Survey associated with this course,
    # then redirect to the course instead
    if not course.course_survey_name:
        return redirect(redirect_url)

    return survey.views.view_student_survey(
        request.user,
        course.course_survey_name,
        course=course,
        redirect_url=redirect_url,
        is_required=course.course_survey_required,
    )


def is_course_passed(course, grade_summary=None, student=None, request=None):
    """
    check user's course passing status. return True if passed

    Arguments:
        course : course object
        grade_summary (dict) : contains student grade details.
        student : user object
        request (HttpRequest)

    Returns:
        returns bool value
    """
    nonzero_cutoffs = [cutoff for cutoff in course.grade_cutoffs.values() if cutoff > 0]
    success_cutoff = min(nonzero_cutoffs) if nonzero_cutoffs else None

    if grade_summary is None:
        grade_summary = CourseGradeFactory(student).create(course).summary

    return success_cutoff and grade_summary['percent'] >= success_cutoff


# Grades can potentially be written - if so, let grading manage the transaction.
@transaction.non_atomic_requests
@require_POST
def generate_user_cert(request, course_id):
    """Start generating a new certificate for the user.

    Certificate generation is allowed if:
    * The user has passed the course, and
    * The user does not already have a pending/completed certificate.

    Note that if an error occurs during certificate generation
    (for example, if the queue is down), then we simply mark the
    certificate generation task status as "error" and re-run
    the task with a management command.  To students, the certificate
    will appear to be "generating" until it is re-run.

    Args:
        request (HttpRequest): The POST request to this view.
        course_id (unicode): The identifier for the course.

    Returns:
        HttpResponse: 200 on success, 400 if a new certificate cannot be generated.

    """

    if not request.user.is_authenticated():
        log.info(u"Anon user trying to generate certificate for %s", course_id)
        return HttpResponseBadRequest(
            _('You must be signed in to {platform_name} to create a certificate.').format(
                platform_name=configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME)
            )
        )

    student = request.user
    course_key = CourseKey.from_string(course_id)

    course = modulestore().get_course(course_key, depth=2)
    if not course:
        return HttpResponseBadRequest(_("Course is not valid"))

    if not is_course_passed(course, None, student, request):
        return HttpResponseBadRequest(_("Your certificate will be available when you pass the course."))

    certificate_status = certs_api.certificate_downloadable_status(student, course.id)

    if certificate_status["is_downloadable"]:
        return HttpResponseBadRequest(_("Certificate has already been created."))
    elif certificate_status["is_generating"]:
        return HttpResponseBadRequest(_("Certificate is being created."))
    else:
        # If the certificate is not already in-process or completed,
        # then create a new certificate generation task.
        # If the certificate cannot be added to the queue, this will
        # mark the certificate with "error" status, so it can be re-run
        # with a management command.  From the user's perspective,
        # it will appear that the certificate task was submitted successfully.
        certs_api.generate_user_certificates(student, course.id, course=course, generation_mode='self')
        _track_successful_certificate_generation(student.id, course.id)
        return HttpResponse()


def _track_successful_certificate_generation(user_id, course_id):  # pylint: disable=invalid-name
    """
    Track a successful certificate generation event.

    Arguments:
        user_id (str): The ID of the user generting the certificate.
        course_id (CourseKey): Identifier for the course.
    Returns:
        None

    """
    if settings.LMS_SEGMENT_KEY:
        event_name = 'edx.bi.user.certificate.generate'
        tracking_context = tracker.get_tracker().resolve_context()

        analytics.track(
            user_id,
            event_name,
            {
                'category': 'certificates',
                'label': unicode(course_id)
            },
            context={
                'ip': tracking_context.get('ip'),
                'Google Analytics': {
                    'clientId': tracking_context.get('client_id')
                }
            }
        )


@require_http_methods(["GET", "POST"])
def render_xblock(request, usage_key_string, check_if_enrolled=True):
    """
    Returns an HttpResponse with HTML content for the xBlock with the given usage_key.
    The returned HTML is a chromeless rendering of the xBlock (excluding content of the containing courseware).
    """
    usage_key = UsageKey.from_string(usage_key_string)
    usage_key = usage_key.replace(course_key=modulestore().fill_in_run(usage_key.course_key))
    course_key = usage_key.course_key

    requested_view = request.GET.get('view', 'student_view')
    if requested_view != 'student_view':
        return HttpResponseBadRequest("Rendering of the xblock view '{}' is not supported.".format(requested_view))

    with modulestore().bulk_operations(course_key):
        # verify the user has access to the course, including enrollment check
        try:
            course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=check_if_enrolled)
        except UserNotEnrolled:
            raise Http404("Course not found.")

        # get the block, which verifies whether the user has access to the block.
        block, _ = get_module_by_usage_id(
            request, unicode(course_key), unicode(usage_key), disable_staff_debug_info=True, course=course
        )

        context = {
            'fragment': block.render('student_view', context=request.GET),
            'course': course,
            'disable_accordion': True,
            'allow_iframing': True,
            'disable_header': True,
            'disable_footer': True,
            'disable_window_wrap': True,
            'disable_preview_menu': True,
            'staff_access': bool(has_access(request.user, 'staff', course)),
            'xqa_server': settings.FEATURES.get('XQA_SERVER', 'http://your_xqa_server.com'),
        }
        return render_to_response('courseware/courseware-chromeless.html', context)


# Translators: "percent_sign" is the symbol "%". "platform_name" is a
# string identifying the name of this installation, such as "edX".
FINANCIAL_ASSISTANCE_HEADER = _(
    '{platform_name} now offers financial assistance for learners who want to earn Verified Certificates but'
    ' who may not be able to pay the Verified Certificate fee. Eligible learners may receive up to 90{percent_sign} off'
    ' the Verified Certificate fee for a course.\nTo apply for financial assistance, enroll in the'
    ' audit track for a course that offers Verified Certificates, and then complete this application.'
    ' Note that you must complete a separate application for each course you take.\n We plan to use this'
    ' information to evaluate your application for financial assistance and to further develop our'
    ' financial assistance program.'
).format(
    percent_sign="%",
    platform_name=configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME)
).split('\n')


FA_INCOME_LABEL = _('Annual Household Income')
FA_REASON_FOR_APPLYING_LABEL = _(
    'Tell us about your current financial situation. Why do you need assistance?'
)
FA_GOALS_LABEL = _(
    'Tell us about your learning or professional goals. How will a Verified Certificate in'
    ' this course help you achieve these goals?'
)
FA_EFFORT_LABEL = _(
    'Tell us about your plans for this course. What steps will you take to help you complete'
    ' the course work and receive a certificate?'
)
FA_SHORT_ANSWER_INSTRUCTIONS = _('Use between 250 and 500 words or so in your response.')


@login_required
def financial_assistance(_request):
    """Render the initial financial assistance page."""
    return render_to_response('financial-assistance/financial-assistance.html', {
        'header_text': FINANCIAL_ASSISTANCE_HEADER
    })


@login_required
@require_POST
def financial_assistance_request(request):
    """Submit a request for financial assistance to Zendesk."""
    try:
        data = json.loads(request.body)
        # Simple sanity check that the session belongs to the user
        # submitting an FA request
        username = data['username']
        if request.user.username != username:
            return HttpResponseForbidden()

        course_id = data['course']
        course = modulestore().get_course(CourseKey.from_string(course_id))
        legal_name = data['name']
        email = data['email']
        country = data['country']
        income = data['income']
        reason_for_applying = data['reason_for_applying']
        goals = data['goals']
        effort = data['effort']
        marketing_permission = data['mktg-permission']
        ip_address = get_ip(request)
    except ValueError:
        # Thrown if JSON parsing fails
        return HttpResponseBadRequest(u'Could not parse request JSON.')
    except InvalidKeyError:
        # Thrown if course key parsing fails
        return HttpResponseBadRequest(u'Could not parse request course key.')
    except KeyError as err:
        # Thrown if fields are missing
        return HttpResponseBadRequest(u'The field {} is required.'.format(err.message))

    zendesk_submitted = _record_feedback_in_zendesk(
        legal_name,
        email,
        u'Financial assistance request for learner {username} in course {course_name}'.format(
            username=username,
            course_name=course.display_name
        ),
        u'Financial Assistance Request',
        {'course_id': course_id},
        # Send the application as additional info on the ticket so
        # that it is not shown when support replies. This uses
        # OrderedDict so that information is presented in the right
        # order.
        OrderedDict((
            ('Username', username),
            ('Full Name', legal_name),
            ('Course ID', course_id),
            ('Annual Household Income', income),
            ('Country', country),
            ('Allowed for marketing purposes', 'Yes' if marketing_permission else 'No'),
            (FA_REASON_FOR_APPLYING_LABEL, '\n' + reason_for_applying + '\n\n'),
            (FA_GOALS_LABEL, '\n' + goals + '\n\n'),
            (FA_EFFORT_LABEL, '\n' + effort + '\n\n'),
            ('Client IP', ip_address),
        )),
        group_name='Financial Assistance',
        require_update=True
    )

    if not zendesk_submitted:
        # The call to Zendesk failed. The frontend will display a
        # message to the user.
        return HttpResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return HttpResponse(status=status.HTTP_204_NO_CONTENT)


@login_required
def financial_assistance_form(request):
    """Render the financial assistance application form page."""
    user = request.user
    enrolled_courses = [
        {'name': enrollment.course_overview.display_name, 'value': unicode(enrollment.course_id)}
        for enrollment in CourseEnrollment.enrollments_for_user(user).order_by('-created')

        if enrollment.mode != CourseMode.VERIFIED and CourseMode.objects.filter(
            Q(_expiration_datetime__isnull=True) | Q(_expiration_datetime__gt=datetime.now(UTC())),
            course_id=enrollment.course_id,
            mode_slug=CourseMode.VERIFIED
        ).exists()
    ]
    incomes = ['Less than $5,000', '$5,000 - $10,000', '$10,000 - $15,000', '$15,000 - $20,000', '$20,000 - $25,000']
    annual_incomes = [
        {'name': _(income), 'value': income} for income in incomes  # pylint: disable=translation-of-non-string
    ]
    return render_to_response('financial-assistance/apply.html', {
        'header_text': FINANCIAL_ASSISTANCE_HEADER,
        'student_faq_url': marketing_link('FAQ'),
        'dashboard_url': reverse('dashboard'),
        'account_settings_url': reverse('account_settings'),
        'platform_name': configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME),
        'user_details': {
            'email': user.email,
            'username': user.username,
            'name': user.profile.name,
            'country': str(user.profile.country.name),
        },
        'submit_url': reverse('submit_financial_assistance_request'),
        'fields': [
            {
                'name': 'course',
                'type': 'select',
                'label': _('Course'),
                'placeholder': '',
                'defaultValue': '',
                'required': True,
                'options': enrolled_courses,
                'instructions': _(
                    'Select the course for which you want to earn a verified certificate. If'
                    ' the course does not appear in the list, make sure that you have enrolled'
                    ' in the audit track for the course.'
                )
            },
            {
                'name': 'income',
                'type': 'select',
                'label': FA_INCOME_LABEL,
                'placeholder': '',
                'defaultValue': '',
                'required': True,
                'options': annual_incomes,
                'instructions': _('Specify your annual household income in US Dollars.')
            },
            {
                'name': 'reason_for_applying',
                'type': 'textarea',
                'label': FA_REASON_FOR_APPLYING_LABEL,
                'placeholder': '',
                'defaultValue': '',
                'required': True,
                'restrictions': {
                    'min_length': settings.FINANCIAL_ASSISTANCE_MIN_LENGTH,
                    'max_length': settings.FINANCIAL_ASSISTANCE_MAX_LENGTH
                },
                'instructions': FA_SHORT_ANSWER_INSTRUCTIONS
            },
            {
                'name': 'goals',
                'type': 'textarea',
                'label': FA_GOALS_LABEL,
                'placeholder': '',
                'defaultValue': '',
                'required': True,
                'restrictions': {
                    'min_length': settings.FINANCIAL_ASSISTANCE_MIN_LENGTH,
                    'max_length': settings.FINANCIAL_ASSISTANCE_MAX_LENGTH
                },
                'instructions': FA_SHORT_ANSWER_INSTRUCTIONS
            },
            {
                'name': 'effort',
                'type': 'textarea',
                'label': FA_EFFORT_LABEL,
                'placeholder': '',
                'defaultValue': '',
                'required': True,
                'restrictions': {
                    'min_length': settings.FINANCIAL_ASSISTANCE_MIN_LENGTH,
                    'max_length': settings.FINANCIAL_ASSISTANCE_MAX_LENGTH
                },
                'instructions': FA_SHORT_ANSWER_INSTRUCTIONS
            },
            {
                'placeholder': '',
                'name': 'mktg-permission',
                'label': _(
                    'I allow edX to use the information provided in this application '
                    '(except for financial information) for edX marketing purposes.'
                ),
                'defaultValue': '',
                'type': 'checkbox',
                'required': False,
                'instructions': '',
                'restrictions': {}
            }
        ],
    })
