import waffle
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from opaque_keys.edx.keys import CourseKey
from six import text_type

from course_modes.models import CourseMode, get_course_prices
from edxmako.shortcuts import marketing_link, render_to_response, render_to_string
from lms.djangoapps.commerce.utils import EcommerceService
from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.courseware.access_utils import check_public_access
from lms.djangoapps.courseware.courses import (
    can_self_enroll_in_course,
    get_course_with_access,
    get_courses,
    get_permission_for_course_about,
    get_studio_url,
    sort_by_announcement,
    sort_by_start_date
)

from lms.djangoapps.courseware.permissions import VIEW_COURSE_HOME, VIEW_COURSEWARE
from lms.djangoapps.courseware.views.index import render_accordion
from lms.djangoapps.courseware.views.views import _course_home_redirect_enabled, registered_for_course
from lms.djangoapps.instructor.enrollment import uses_shib
from openedx.core.djangoapps.catalog.utils import get_programs_with_type
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.enrollments.permissions import ENROLL_IN_COURSE
from openedx.core.djangoapps.models.course_details import CourseDetails
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.features.course_experience import course_home_url_name
from openedx.features.course_experience.utils import get_course_outline_block_tree
from openedx.features.course_experience.waffle import ENABLE_COURSE_ABOUT_SIDEBAR_HTML
from openedx.features.course_experience.waffle import waffle as course_experience_waffle
from openedx.features.pakx.cms.custom_settings.models import CourseOverviewContent
from openedx.features.pakx.lms.overrides.utils import add_course_progress_and_resume_info_tags_to_enrolled_courses
from student.models import CourseEnrollment
from util.cache import cache_if_anonymous
from util.milestones_helpers import get_prerequisite_courses_display
from util.views import ensure_valid_course_key
from xmodule.course_module import COURSE_VISIBILITY_PUBLIC, COURSE_VISIBILITY_PUBLIC_OUTLINE
from xmodule.modulestore.django import modulestore


@ensure_csrf_cookie
@login_required
def courses(request, section='in-progress'):
    """
    Render "find courses" page. The course selection work is done in courseware.courses.

    If the marketing site is enabled, redirect to that. Otherwise, if subdomain
    branding is on, this is the university profile page. Otherwise, it's the edX
    courseware.views.views.courses page

    Arguments:
          request (WSGIRequest): HTTP request object
          section (str): 'in-progress'/'upcoming'/'complete'
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
    courses_list = []
    course_discovery_meanings = getattr(settings, 'COURSE_DISCOVERY_MEANINGS', {})
    if not settings.FEATURES.get('ENABLE_COURSE_DISCOVERY'):
        courses_list = get_courses(request.user)

        if configuration_helpers.get_value("ENABLE_COURSE_SORTING_BY_START_DATE",
                                           settings.FEATURES["ENABLE_COURSE_SORTING_BY_START_DATE"]):
            courses_list = sort_by_start_date(courses_list)
        else:
            courses_list = sort_by_announcement(courses_list)

    # split courses into categories i.e upcoming & in-progress
    in_progress_courses = []
    upcoming_courses = []
    completed_courses = []

    add_course_progress_and_resume_info_tags_to_enrolled_courses(request, courses_list)

    show_only_enrolled_courses = waffle.switch_is_active('show_only_enrolled_courses')

    for course in courses_list:
        if show_only_enrolled_courses and not course.enrolled:
            continue
        if course.user_progress == '100':
            completed_courses.append(course)
        elif course.has_started():
            in_progress_courses.append(course)
        else:
            upcoming_courses.append(course)

    # Add marketable programs to the context.
    programs_list = get_programs_with_type(request.site, include_hidden=False)

    return render_to_response(
        "courseware/courses.html",
        {
            'in_progress_courses': in_progress_courses,
            'upcoming_courses': upcoming_courses,
            'completed_courses': completed_courses,
            'course_discovery_meanings': course_discovery_meanings,
            'programs_list': programs_list,
            'section': section,
            'show_only_enrolled_courses': show_only_enrolled_courses
        }
    )


@ensure_csrf_cookie
@login_required
def overview_tab_view(request, course_id=None):
    course_key = CourseKey.from_string(course_id)
    course = get_course_with_access(request.user, 'load', course_key)
    course_block_tree = get_course_outline_block_tree(
        request, text_type(course_id), request.user, allow_start_dates_in_future=True
    )
    course_overview_content = CourseOverviewContent.objects.filter(course_id=course_key).first()
    context = {
        'course_overview':  course_overview_content.body_html if course_overview_content else None,
        'user': request.user,
        'course': course,
        'accordion': render_accordion(request, course, course_block_tree, '', '')
    }
    return render_to_response('courseware/overview.html', context)


# noinspection PyInterpreter
@ensure_csrf_cookie
@ensure_valid_course_key
@cache_if_anonymous()
def course_about(request, category, course_id):
    """
    Display the course's about page.

    Arguments:
        request (WSGIRequest): HTTP request
        course_id (str): Unique ID of course
        category (str): 'In Progress'/'Upcoming'/'Completed'
    """
    course_key = CourseKey.from_string(course_id)

    # If a user is not able to enroll in a course then redirect
    # them away from the about page to the dashboard.
    if not can_self_enroll_in_course(course_key):
        return redirect(reverse('dashboard'))

    # If user needs to be redirected to course home then redirect
    if _course_home_redirect_enabled():
        return redirect(reverse(course_home_url_name(course_key), args=[text_type(course_key)]))

    with modulestore().bulk_operations(course_key):
        permission = get_permission_for_course_about()
        course = get_course_with_access(request.user, permission, course_key)
        course_details = CourseDetails.populate(course)
        modes = CourseMode.modes_for_course_dict(course_key)
        registered = registered_for_course(course, request.user)

        staff_access = bool(has_access(request.user, 'staff', course))
        studio_url = get_studio_url(course, 'settings/details')

        if request.user.has_perm(VIEW_COURSE_HOME, course):
            course_target = reverse(course_home_url_name(course.id), args=[text_type(course.id)])
        else:
            course_target = reverse('about_course', args=[text_type(course.id)])

        show_courseware_link = bool(
            (
                request.user.has_perm(VIEW_COURSEWARE, course)
            ) or settings.FEATURES.get('ENABLE_LMS_MIGRATION')
        )

        # If the ecommerce checkout flow is enabled and the mode of the course is
        # professional or no id professional, we construct links for the enrollment
        # button to add the course to the ecommerce basket.
        ecomm_service = EcommerceService()
        ecommerce_checkout = ecomm_service.is_enabled(request.user)
        ecommerce_checkout_link = ''
        ecommerce_bulk_checkout_link = ''
        single_paid_mode = None
        if ecommerce_checkout:
            if len(modes) == 1 and list(modes.values())[0].min_price:
                single_paid_mode = list(modes.values())[0]
            else:
                # have professional ignore other modes for historical reasons
                single_paid_mode = modes.get(CourseMode.PROFESSIONAL)

            if single_paid_mode and single_paid_mode.sku:
                ecommerce_checkout_link = ecomm_service.get_checkout_page_url(single_paid_mode.sku)
            if single_paid_mode and single_paid_mode.bulk_sku:
                ecommerce_bulk_checkout_link = ecomm_service.get_checkout_page_url(single_paid_mode.bulk_sku)

        registration_price, course_price = get_course_prices(course)

        # Used to provide context to message to student if enrollment not allowed
        can_enroll = bool(request.user.has_perm(ENROLL_IN_COURSE, course))
        invitation_only = course.invitation_only
        is_course_full = CourseEnrollment.objects.is_course_full(course)

        # Register button should be disabled if one of the following is true:
        # - Student is already registered for course
        # - Course is already full
        # - Student cannot enroll in course
        active_reg_button = not (registered or is_course_full or not can_enroll)

        is_shib_course = uses_shib(course)

        # get prerequisite courses display names
        pre_requisite_courses = get_prerequisite_courses_display(course)

        # Overview
        overview = CourseOverview.get_from_id(course.id)

        sidebar_html_enabled = course_experience_waffle().is_enabled(ENABLE_COURSE_ABOUT_SIDEBAR_HTML)

        allow_anonymous = check_public_access(course, [COURSE_VISIBILITY_PUBLIC, COURSE_VISIBILITY_PUBLIC_OUTLINE])

        # This local import is due to the circularity of lms and openedx references.
        # This may be resolved by using stevedore to allow web fragments to be used
        # as plugins, and to avoid the direct import.
        from openedx.features.course_experience.views.course_reviews import CourseReviewsModuleFragmentView

        # Embed the course reviews tool
        reviews_fragment_view = CourseReviewsModuleFragmentView().render_to_fragment(request, course=course)

        context = {
            'course': course,
            'course_details': course_details,
            'staff_access': staff_access,
            'studio_url': studio_url,
            'registered': registered,
            'course_target': course_target,
            'is_cosmetic_price_enabled': settings.FEATURES.get('ENABLE_COSMETIC_DISPLAY_PRICE'),
            'course_price': course_price,
            'ecommerce_checkout': ecommerce_checkout,
            'ecommerce_checkout_link': ecommerce_checkout_link,
            'ecommerce_bulk_checkout_link': ecommerce_bulk_checkout_link,
            'single_paid_mode': single_paid_mode,
            'show_courseware_link': show_courseware_link,
            'is_course_full': is_course_full,
            'can_enroll': can_enroll,
            'invitation_only': invitation_only,
            'active_reg_button': active_reg_button,
            'is_shib_course': is_shib_course,
            # We do not want to display the internal courseware header, which is used when the course is found in the
            # context. This value is therefor explicitly set to render the appropriate header.
            'disable_courseware_header': True,
            'pre_requisite_courses': pre_requisite_courses,
            'course_image_urls': overview.image_urls,
            'reviews_fragment_view': reviews_fragment_view,
            'sidebar_html_enabled': sidebar_html_enabled,
            'allow_anonymous': allow_anonymous,
            'category': category
        }

        return render_to_response('courseware/course_about.html', context)
