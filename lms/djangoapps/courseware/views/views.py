"""
Courseware views functions
"""


import json
import logging
from collections import OrderedDict, namedtuple
from datetime import datetime

import bleach
import requests
import six
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q, prefetch_related_objects
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import redirect
from django.template.context_processors import csrf
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.http import urlquote_plus
from django.utils.text import slugify
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_noop
from django.views.decorators.cache import cache_control
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django.views.generic import View
from edx_django_utils import monitoring as monitoring_utils
from edx_django_utils.monitoring import set_custom_attributes_for_course_key
from ipware.ip import get_ip
from markupsafe import escape
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey
from pytz import UTC
from requests.exceptions import ConnectionError, Timeout  # pylint: disable=redefined-builtin
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from six import text_type
from web_fragments.fragment import Fragment

from lms.djangoapps.survey import views as survey_views
from common.djangoapps.course_modes.models import CourseMode, get_course_prices
from common.djangoapps.edxmako.shortcuts import marketing_link, render_to_response, render_to_string
from lms.djangoapps.edxnotes.helpers import is_feature_enabled
from lms.djangoapps.ccx.custom_exception import CCXLocatorValidationException
from lms.djangoapps.certificates import api as certs_api
from lms.djangoapps.certificates.models import CertificateStatuses
from lms.djangoapps.commerce.utils import EcommerceService
from lms.djangoapps.course_home_api.utils import is_request_from_learning_mfe
from lms.djangoapps.courseware.access import has_access, has_ccx_coach_role
from lms.djangoapps.courseware.access_utils import check_course_open_for_learner, check_public_access
from lms.djangoapps.courseware.courses import (
    can_self_enroll_in_course,
    course_open_for_self_enrollment,
    get_course,
    get_course_date_blocks,
    get_course_overview_with_access,
    get_course_with_access,
    get_courses,
    get_current_child,
    get_permission_for_course_about,
    get_studio_url,
    sort_by_announcement,
    sort_by_start_date
)
from lms.djangoapps.courseware.date_summary import verified_upgrade_deadline_link
from lms.djangoapps.courseware.exceptions import CourseAccessRedirect, Redirect
from lms.djangoapps.courseware.masquerade import setup_masquerade
from lms.djangoapps.courseware.model_data import FieldDataCache
from lms.djangoapps.courseware.models import BaseStudentModuleHistory, StudentModule
from lms.djangoapps.courseware.permissions import (
    MASQUERADE_AS_STUDENT,
    VIEW_COURSE_HOME,
    VIEW_COURSEWARE,
    VIEW_XQA_INTERFACE
)
from lms.djangoapps.courseware.url_helpers import get_redirect_url
from lms.djangoapps.courseware.user_state_client import DjangoXBlockUserStateClient
from lms.djangoapps.experiments.utils import get_experiment_user_metadata_context
from lms.djangoapps.grades.api import CourseGradeFactory
from lms.djangoapps.instructor.enrollment import uses_shib
from lms.djangoapps.instructor.views.api import require_global_staff
from lms.djangoapps.verify_student.services import IDVerificationService
from openedx.core.djangoapps.catalog.utils import get_programs, get_programs_with_type
from openedx.core.djangoapps.certificates import api as auto_certs_api
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.credit.api import (
    get_credit_requirement_status,
    is_credit_course,
    is_user_eligible_for_credit
)
from openedx.core.djangoapps.enrollments.api import add_enrollment, get_enrollment
from openedx.core.djangoapps.enrollments.permissions import ENROLL_IN_COURSE
from openedx.core.djangoapps.models.course_details import CourseDetails
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from openedx.core.djangoapps.programs.utils import ProgramMarketingDataExtender
from openedx.core.djangoapps.self_paced.models import SelfPacedConfiguration
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.util.user_messages import PageLevelMessages
from openedx.core.djangoapps.zendesk_proxy.utils import create_zendesk_ticket
from openedx.core.djangolib.markup import HTML, Text
from openedx.core.lib.mobile_utils import is_request_from_mobile_app
from openedx.features.content_type_gating.models import ContentTypeGatingConfig
from openedx.features.course_duration_limits.access import generate_course_expired_fragment
from openedx.features.course_experience import DISABLE_UNIFIED_COURSE_TAB_FLAG, course_home_url_name
from openedx.features.course_experience.course_tools import CourseToolsPluginManager
from openedx.features.course_experience.utils import dates_banner_should_display
from openedx.features.course_experience.views.course_dates import CourseDatesFragmentView
from openedx.features.course_experience.waffle import ENABLE_COURSE_ABOUT_SIDEBAR_HTML
from openedx.features.course_experience.waffle import waffle as course_experience_waffle
from openedx.features.enterprise_support.api import data_sharing_consent_required
from common.djangoapps.student.models import CourseEnrollment, UserTestGroup
from common.djangoapps.track import segment
from common.djangoapps.util.cache import cache, cache_if_anonymous
from common.djangoapps.util.db import outer_atomic
from common.djangoapps.util.milestones_helpers import get_prerequisite_courses_display
from common.djangoapps.util.views import ensure_valid_course_key, ensure_valid_usage_key
from xmodule.course_module import COURSE_VISIBILITY_PUBLIC, COURSE_VISIBILITY_PUBLIC_OUTLINE
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError, NoPathToItem
from xmodule.tabs import CourseTabList
from xmodule.x_module import STUDENT_VIEW

from ..context_processor import user_timezone_locale_prefs
from ..entrance_exams import user_can_skip_entrance_exam
from ..module_render import get_module, get_module_by_usage_id, get_module_for_descriptor

log = logging.getLogger("edx.courseware")


# Only display the requirements on learner dashboard for
# credit and verified modes.
REQUIREMENTS_DISPLAY_MODES = CourseMode.CREDIT_MODES + [CourseMode.VERIFIED]

CertData = namedtuple(
    "CertData", ["cert_status", "title", "msg", "download_url", "cert_web_view_url"]
)
EARNED_BUT_NOT_AVAILABLE_CERT_STATUS = 'earned_but_not_available'

AUDIT_PASSING_CERT_DATA = CertData(
    CertificateStatuses.audit_passing,
    _('Your enrollment: Audit track'),
    _('You are enrolled in the audit track for this course. The audit track does not include a certificate.'),
    download_url=None,
    cert_web_view_url=None
)

HONOR_PASSING_CERT_DATA = CertData(
    CertificateStatuses.honor_passing,
    _('Your enrollment: Honor track'),
    _('You are enrolled in the honor track for this course. The honor track does not include a certificate.'),
    download_url=None,
    cert_web_view_url=None
)

INELIGIBLE_PASSING_CERT_DATA = {
    CourseMode.AUDIT: AUDIT_PASSING_CERT_DATA,
    CourseMode.HONOR: HONOR_PASSING_CERT_DATA
}

GENERATING_CERT_DATA = CertData(
    CertificateStatuses.generating,
    _("We're working on it..."),
    _(
        "We're creating your certificate. You can keep working in your courses and a link "
        "to it will appear here and on your Dashboard when it is ready."
    ),
    download_url=None,
    cert_web_view_url=None
)

INVALID_CERT_DATA = CertData(
    CertificateStatuses.invalidated,
    _('Your certificate has been invalidated'),
    _('Please contact your course team if you have any questions.'),
    download_url=None,
    cert_web_view_url=None
)

REQUESTING_CERT_DATA = CertData(
    CertificateStatuses.requesting,
    _('Congratulations, you qualified for a certificate!'),
    _("You've earned a certificate for this course."),
    download_url=None,
    cert_web_view_url=None
)

UNVERIFIED_CERT_DATA = CertData(
    CertificateStatuses.unverified,
    _('Certificate unavailable'),
    _(
        u'You have not received a certificate because you do not have a current {platform_name} '
        'verified identity.'
    ).format(platform_name=configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME)),
    download_url=None,
    cert_web_view_url=None
)

EARNED_BUT_NOT_AVAILABLE_CERT_DATA = CertData(
    EARNED_BUT_NOT_AVAILABLE_CERT_STATUS,
    _('Your certificate will be available soon!'),
    _('After this course officially ends, you will receive an email notification with your certificate.'),
    download_url=None,
    cert_web_view_url=None
)


def _downloadable_cert_data(download_url=None, cert_web_view_url=None):
    return CertData(
        CertificateStatuses.downloadable,
        _('Your certificate is available'),
        _("You've earned a certificate for this course."),
        download_url=download_url,
        cert_web_view_url=cert_web_view_url
    )


def user_groups(user):
    """
    TODO (vshnayder): This is not used. When we have a new plan for groups, adjust appropriately.
    """
    if not user.is_authenticated:
        return []

    # TODO: Rewrite in Django
    key = 'user_group_names_{user.id}'.format(user=user)
    cache_expiration = 60 * 60  # one hour

    # Kill caching on dev machines -- we switch groups a lot
    group_names = cache.get(key)
    if settings.DEBUG:
        group_names = None

    if group_names is None:
        group_names = [u.name for u in UserTestGroup.objects.filter(users=user)]
        cache.set(key, group_names, cache_expiration)

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

        if configuration_helpers.get_value("ENABLE_COURSE_SORTING_BY_START_DATE",
                                           settings.FEATURES["ENABLE_COURSE_SORTING_BY_START_DATE"]):
            courses_list = sort_by_start_date(courses_list)
        else:
            courses_list = sort_by_announcement(courses_list)

    # Add marketable programs to the context.
    programs_list = get_programs_with_type(request.site, include_hidden=False)

    return render_to_response(
        "courseware/courses.html",
        {
            'courses': courses_list,
            'course_discovery_meanings': course_discovery_meanings,
            'programs_list': programs_list,
        }
    )


class PerUserVideoMetadataThrottle(UserRateThrottle):
    """
    setting rate limit for  yt_video_metadata API
    """
    rate = settings.RATE_LIMIT_FOR_VIDEO_METADATA_API


@ensure_csrf_cookie
@login_required
@api_view(['GET'])
@throttle_classes([PerUserVideoMetadataThrottle])
def yt_video_metadata(request):
    """
    Will hit the youtube API if the key is available in settings
    :return: youtube video metadata
    """
    video_id = request.GET.get('id', None)
    metadata, status_code = load_metadata_from_youtube(video_id, request)
    return Response(metadata, status=status_code, content_type='application/json')


def load_metadata_from_youtube(video_id, request):
    """
    Get metadata about a YouTube video.

    This method is used via the standalone /courses/yt_video_metadata REST API
    endpoint, or via the video XBlock as a its 'yt_video_metadata' handler.
    """
    metadata = {}
    status_code = 500
    if video_id and settings.YOUTUBE_API_KEY and settings.YOUTUBE_API_KEY != 'PUT_YOUR_API_KEY_HERE':
        yt_api_key = settings.YOUTUBE_API_KEY
        yt_metadata_url = settings.YOUTUBE['METADATA_URL']
        yt_timeout = settings.YOUTUBE.get('TEST_TIMEOUT', 1500) / 1000  # converting milli seconds to seconds

        headers = {}
        http_referer = None

        try:
            # This raises an attribute error if called from the xblock yt_video_metadata handler, which passes
            # a webob request instead of a django request.
            http_referer = request.META.get('HTTP_REFERER')
        except AttributeError:
            # So here, let's assume it's a webob request and access the referer the webob way.
            http_referer = request.referer

        if http_referer:
            headers['Referer'] = http_referer

        payload = {'id': video_id, 'part': 'contentDetails', 'key': yt_api_key}
        try:
            res = requests.get(yt_metadata_url, params=payload, timeout=yt_timeout, headers=headers)
            status_code = res.status_code
            if res.status_code == 200:
                try:
                    res_json = res.json()
                    if res_json.get('items', []):
                        metadata = res_json
                    else:
                        logging.warning(u'Unable to find the items in response. Following response '
                                        u'was received: {res}'.format(res=res.text))
                except ValueError:
                    logging.warning(u'Unable to decode response to json. Following response '
                                    u'was received: {res}'.format(res=res.text))
            else:
                logging.warning(u'YouTube API request failed with status code={status} - '
                                u'Error message is={message}'.format(status=status_code, message=res.text))
        except (Timeout, ConnectionError):
            logging.warning(u'YouTube API request failed because of connection time out or connection error')
    else:
        logging.warning(u'YouTube API key or video id is None. Please make sure API key and video id is not None')

    return metadata, status_code


@ensure_csrf_cookie
@ensure_valid_course_key
def jump_to_id(request, course_id, module_id):
    """
    This entry point allows for a shorter version of a jump to where just the id of the element is
    passed in. This assumes that id is unique within the course_id namespace
    """
    course_key = CourseKey.from_string(course_id)
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
            text_type(items[0].location)
        )

    return jump_to(request, course_id, text_type(items[0].location))


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
        redirect_url = get_redirect_url(course_key, usage_key, _request)
    except ItemNotFoundError:
        raise Http404(u"No data at this location: {0}".format(usage_key))
    except NoPathToItem:
        raise Http404(u"This location is not in any class: {0}".format(usage_key))

    return redirect(redirect_url)


@ensure_csrf_cookie
@ensure_valid_course_key
@data_sharing_consent_required
def course_info(request, course_id):
    """
    Display the course's info.html, or 404 if there is no such course.
    Assumes the course_id is in a valid format.
    """
    # TODO: LEARNER-611: This can be deleted with Course Info removal.  The new
    #    Course Home is using its own processing of last accessed.
    def get_last_accessed_courseware(course, request, user):
        """
        Returns the courseware module URL that the user last accessed, or None if it cannot be found.
        """
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            course.id, request.user, course, depth=2
        )
        course_module = get_module_for_descriptor(
            user,
            request,
            course,
            field_data_cache,
            course.id,
            course=course,
            will_recheck_access=True,
        )
        chapter_module = get_current_child(course_module)
        if chapter_module is not None:
            section_module = get_current_child(chapter_module)
            if section_module is not None:
                url = reverse('courseware_section', kwargs={
                    'course_id': text_type(course.id),
                    'chapter': chapter_module.url_name,
                    'section': section_module.url_name
                })
                return url
        return None

    course_key = CourseKey.from_string(course_id)

    # If the unified course experience is enabled, redirect to the "Course" tab
    if not DISABLE_UNIFIED_COURSE_TAB_FLAG.is_enabled(course_key):
        return redirect(reverse(course_home_url_name(course_key), args=[course_id]))

    with modulestore().bulk_operations(course_key):
        course = get_course_with_access(request.user, 'load', course_key)

        can_masquerade = request.user.has_perm(MASQUERADE_AS_STUDENT, course)
        masquerade, user = setup_masquerade(request, course_key, can_masquerade, reset_masquerade_data=True)

        # LEARNER-612: CCX redirect handled by new Course Home (DONE)
        # LEARNER-1697: Transition banner messages to new Course Home (DONE)
        # if user is not enrolled in a course then app will show enroll/get register link inside course info page.
        user_is_enrolled = CourseEnrollment.is_enrolled(user, course.id)
        show_enroll_banner = request.user.is_authenticated and not user_is_enrolled

        # If the user is not enrolled but this is a course that does not support
        # direct enrollment then redirect them to the dashboard.
        if not user_is_enrolled and not can_self_enroll_in_course(course_key):
            return redirect(reverse('dashboard'))

        # LEARNER-170: Entrance exam is handled by new Course Outline. (DONE)
        # If the user needs to take an entrance exam to access this course, then we'll need
        # to send them to that specific course module before allowing them into other areas
        if not user_can_skip_entrance_exam(user, course):
            return redirect(reverse('courseware', args=[text_type(course.id)]))

        # Construct the dates fragment
        dates_fragment = None

        if request.user.is_authenticated:
            # TODO: LEARNER-611: Remove enable_course_home_improvements
            if SelfPacedConfiguration.current().enable_course_home_improvements:
                # Shared code with the new Course Home (DONE)
                dates_fragment = CourseDatesFragmentView().render_to_fragment(request, course_id=course_id)

        # This local import is due to the circularity of lms and openedx references.
        # This may be resolved by using stevedore to allow web fragments to be used
        # as plugins, and to avoid the direct import.
        from openedx.features.course_experience.views.course_reviews import CourseReviewsModuleFragmentView

        # Shared code with the new Course Home (DONE)
        # Get the course tools enabled for this user and course
        course_tools = CourseToolsPluginManager.get_enabled_course_tools(request, course_key)

        course_homepage_invert_title =\
            configuration_helpers.get_value(
                'COURSE_HOMEPAGE_INVERT_TITLE',
                False
            )

        course_homepage_show_subtitle =\
            configuration_helpers.get_value(
                'COURSE_HOMEPAGE_SHOW_SUBTITLE',
                True
            )

        course_homepage_show_org =\
            configuration_helpers.get_value('COURSE_HOMEPAGE_SHOW_ORG', True)

        course_title = course.display_number_with_default
        course_subtitle = course.display_name_with_default
        if course_homepage_invert_title:
            course_title = course.display_name_with_default
            course_subtitle = course.display_number_with_default

        context = {
            'request': request,
            'masquerade_user': user,
            'course_id': text_type(course_key),
            'url_to_enroll': CourseTabView.url_to_enroll(course_key),
            'cache': None,
            'course': course,
            'course_title': course_title,
            'course_subtitle': course_subtitle,
            'show_subtitle': course_homepage_show_subtitle,
            'show_org': course_homepage_show_org,
            'can_masquerade': can_masquerade,
            'masquerade': masquerade,
            'supports_preview_menu': True,
            'studio_url': get_studio_url(course, 'course_info'),
            'show_enroll_banner': show_enroll_banner,
            'user_is_enrolled': user_is_enrolled,
            'dates_fragment': dates_fragment,
            'course_tools': course_tools,
        }
        context.update(
            get_experiment_user_metadata_context(
                course,
                user,
            )
        )

        # Get the URL of the user's last position in order to display the 'where you were last' message
        context['resume_course_url'] = None
        # TODO: LEARNER-611: Remove enable_course_home_improvements
        if SelfPacedConfiguration.current().enable_course_home_improvements:
            context['resume_course_url'] = get_last_accessed_courseware(course, request, user)

        if not check_course_open_for_learner(user, course):
            # Disable student view button if user is staff and
            # course is not yet visible to students.
            context['disable_student_access'] = True
            context['supports_preview_menu'] = False

        return render_to_response('courseware/info.html', context)


class StaticCourseTabView(EdxFragmentView):
    """
    View that displays a static course tab with a given name.
    """
    @method_decorator(ensure_csrf_cookie)
    @method_decorator(ensure_valid_course_key)
    def get(self, request, course_id, tab_slug, **kwargs):
        """
        Displays a static course tab page with a given name
        """
        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, 'load', course_key)
        tab = CourseTabList.get_tab_by_slug(course.tabs, tab_slug)
        if tab is None:
            raise Http404

        # Show warnings if the user has limited access
        CourseTabView.register_user_access_warning_messages(request, course)

        return super(StaticCourseTabView, self).get(request, course=course, tab=tab, **kwargs)

    def render_to_fragment(self, request, course=None, tab=None, **kwargs):
        """
        Renders the static tab to a fragment.
        """
        return get_static_tab_fragment(request, course, tab)

    def render_standalone_response(self, request, fragment, course=None, tab=None, **kwargs):
        """
        Renders this static tab's fragment to HTML for a standalone page.
        """
        return render_to_response('courseware/static_tab.html', {
            'course': course,
            'active_page': 'static_tab_{0}'.format(tab['url_slug']),
            'tab': tab,
            'fragment': fragment,
            'disable_courseware_js': True,
        })


class CourseTabView(EdxFragmentView):
    """
    View that displays a course tab page.
    """
    @method_decorator(ensure_csrf_cookie)
    @method_decorator(ensure_valid_course_key)
    @method_decorator(data_sharing_consent_required)
    def get(self, request, course_id, tab_type, **kwargs):
        """
        Displays a course tab page that contains a web fragment.
        """
        course_key = CourseKey.from_string(course_id)
        with modulestore().bulk_operations(course_key):
            course = get_course_with_access(request.user, 'load', course_key)
            try:
                # Render the page
                tab = CourseTabList.get_tab_by_type(course.tabs, tab_type)
                page_context = self.create_page_context(request, course=course, tab=tab, **kwargs)

                # Show warnings if the user has limited access
                # Must come after masquerading on creation of page context
                self.register_user_access_warning_messages(request, course)

                set_custom_attributes_for_course_key(course_key)
                return super(CourseTabView, self).get(request, course=course, page_context=page_context, **kwargs)
            except Exception as exception:  # pylint: disable=broad-except
                return CourseTabView.handle_exceptions(request, course_key, course, exception)

    @staticmethod
    def url_to_enroll(course_key):
        """
        Returns the URL to use to enroll in the specified course.
        """
        url_to_enroll = reverse('about_course', args=[text_type(course_key)])
        if settings.FEATURES.get('ENABLE_MKTG_SITE'):
            url_to_enroll = marketing_link('COURSES')
        return url_to_enroll

    @staticmethod
    def register_user_access_warning_messages(request, course):
        """
        Register messages to be shown to the user if they have limited access.
        """
        allow_anonymous = check_public_access(course, [COURSE_VISIBILITY_PUBLIC])

        if request.user.is_anonymous and not allow_anonymous:
            if CourseTabView.course_open_for_learner_enrollment(course):
                PageLevelMessages.register_warning_message(
                    request,
                    Text(_(u"To see course content, {sign_in_link} or {register_link}.")).format(
                        sign_in_link=HTML(u'<a href="/login?next={current_url}">{sign_in_label}</a>').format(
                            sign_in_label=_("sign in"),
                            current_url=urlquote_plus(request.path),
                        ),
                        register_link=HTML(u'<a href="/register?next={current_url}">{register_label}</a>').format(
                            register_label=_("register"),
                            current_url=urlquote_plus(request.path),
                        ),
                    )
                )
            else:
                PageLevelMessages.register_warning_message(
                    request,
                    Text(_(u"{sign_in_link} or {register_link}.")).format(
                        sign_in_link=HTML(u'<a href="/login?next={current_url}">{sign_in_label}</a>').format(
                            sign_in_label=_("Sign in"),
                            current_url=urlquote_plus(request.path),
                        ),
                        register_link=HTML(u'<a href="/register?next={current_url}">{register_label}</a>').format(
                            register_label=_("register"),
                            current_url=urlquote_plus(request.path),
                        ),
                    )
                )
        else:
            if not CourseEnrollment.is_enrolled(request.user, course.id) and not allow_anonymous:
                # Only show enroll button if course is open for enrollment.
                if CourseTabView.course_open_for_learner_enrollment(course):
                    enroll_message = _(u'You must be enrolled in the course to see course content. \
                            {enroll_link_start}Enroll now{enroll_link_end}.')
                    PageLevelMessages.register_warning_message(
                        request,
                        Text(enroll_message).format(
                            enroll_link_start=HTML('<button class="enroll-btn btn-link">'),
                            enroll_link_end=HTML('</button>')
                        )
                    )
                else:
                    PageLevelMessages.register_warning_message(
                        request,
                        Text(_('You must be enrolled in the course to see course content.'))
                    )

    @staticmethod
    def course_open_for_learner_enrollment(course):
        return (course_open_for_self_enrollment(course.id)
                and not course.invitation_only
                and not CourseMode.is_masters_only(course.id))

    @staticmethod
    def handle_exceptions(request, course_key, course, exception):
        u"""
        Handle exceptions raised when rendering a view.
        """
        if isinstance(exception, Redirect) or isinstance(exception, Http404):
            raise
        if settings.DEBUG:
            raise
        user = request.user
        log.exception(
            u"Error in %s: user=%s, effective_user=%s, course=%s",
            request.path,
            getattr(user, 'real_user', user),
            user,
            text_type(course_key),
        )
        try:
            return render_to_response(
                'courseware/courseware-error.html',
                {
                    'staff_access': has_access(user, 'staff', course),
                    'course': course,
                },
                status=500,
            )
        except:
            # Let the exception propagate, relying on global config to
            # at least return a nice error message
            log.exception("Error while rendering courseware-error page")
            raise

    def create_page_context(self, request, course=None, tab=None, **kwargs):
        """
        Creates the context for the fragment's template.
        """
        can_masquerade = request.user.has_perm(MASQUERADE_AS_STUDENT, course)
        supports_preview_menu = tab.get('supports_preview_menu', False)
        if supports_preview_menu:
            masquerade, masquerade_user = setup_masquerade(
                request,
                course.id,
                can_masquerade,
                reset_masquerade_data=True,
            )
            request.user = masquerade_user
        else:
            masquerade = None

        context = {
            'course': course,
            'tab': tab,
            'active_page': tab.get('type', None),
            'can_masquerade': can_masquerade,
            'masquerade': masquerade,
            'supports_preview_menu': supports_preview_menu,
            'uses_bootstrap': True,
            'disable_courseware_js': True,
        }
        # Avoid Multiple Mathjax loading on the 'user_profile'
        if 'profile_page_context' in kwargs:
            context['load_mathjax'] = kwargs['profile_page_context'].get('load_mathjax', True)

        context.update(
            get_experiment_user_metadata_context(
                course,
                request.user,
            )
        )
        return context

    def render_to_fragment(self, request, course=None, page_context=None, **kwargs):
        """
        Renders the course tab to a fragment.
        """
        tab = page_context['tab']
        return tab.render_to_fragment(request, course, **kwargs)

    def render_standalone_response(self, request, fragment, course=None, tab=None, page_context=None, **kwargs):
        """
        Renders this course tab's fragment to HTML for a standalone page.
        """
        if not page_context:
            page_context = self.create_page_context(request, course=course, tab=tab, **kwargs)
        tab = page_context['tab']
        page_context['fragment'] = fragment
        return render_to_response('courseware/tab-view.html', page_context)


@ensure_csrf_cookie
@ensure_valid_course_key
def syllabus(request, course_id):
    """
    Display the course's syllabus.html, or 404 if there is no such course.
    Assumes the course_id is in a valid format.
    """

    course_key = CourseKey.from_string(course_id)

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
    if user.is_authenticated:
        return CourseEnrollment.is_enrolled(user, course.id)
    else:
        return False


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
        _next = six.moves.urllib.parse.quote_plus(request.GET.get('next', 'info'), safe='/:?=')
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
        return redirect(reverse('about_course', args=[text_type(course_key)]))


@ensure_csrf_cookie
@ensure_valid_course_key
@cache_if_anonymous()
def course_about(request, course_id):
    """
    Display the course's about page.
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
        }

        return render_to_response('courseware/course_about.html', context)


@ensure_csrf_cookie
@cache_if_anonymous()
def program_marketing(request, program_uuid):
    """
    Display the program marketing page.
    """
    program_data = get_programs(uuid=program_uuid)

    if not program_data:
        raise Http404

    program = ProgramMarketingDataExtender(program_data, request.user).extend()
    program['type_slug'] = slugify(program['type'])
    skus = program.get('skus')
    ecommerce_service = EcommerceService()

    context = {'program': program}

    if program.get('is_learner_eligible_for_one_click_purchase') and skus:
        context['buy_button_href'] = ecommerce_service.get_checkout_page_url(*skus, program_uuid=program_uuid)

    context['uses_bootstrap'] = True

    return render_to_response('courseware/program_marketing.html', context)


@login_required
@ensure_csrf_cookie
@ensure_valid_course_key
def dates(request, course_id):
    """
    Display the course's dates.html, or 404 if there is no such course.
    Assumes the course_id is in a valid format.
    """
    from lms.urls import COURSE_DATES_NAME, RESET_COURSE_DEADLINES_NAME

    course_key = CourseKey.from_string(course_id)

    # Enable NR tracing for this view based on course
    monitoring_utils.set_custom_attribute('course_id', text_type(course_key))
    monitoring_utils.set_custom_attribute('user_id', request.user.id)
    monitoring_utils.set_custom_attribute('is_staff', request.user.is_staff)

    course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=False)

    masquerade = None
    can_masquerade = request.user.has_perm(MASQUERADE_AS_STUDENT, course)
    if can_masquerade:
        masquerade, masquerade_user = setup_masquerade(
            request,
            course.id,
            can_masquerade,
            reset_masquerade_data=True,
        )
        request.user = masquerade_user

    user_is_enrolled = CourseEnrollment.is_enrolled(request.user, course_key)
    user_is_staff = bool(has_access(request.user, 'staff', course_key))

    # Render the full content to enrolled users, as well as to course and global staff.
    # Unenrolled users who are not course or global staff are redirected to the Outline Tab.
    if not user_is_enrolled and not user_is_staff:
        raise CourseAccessRedirect(reverse('openedx.course_experience.course_home', args=[course_id]))

    course_date_blocks = get_course_date_blocks(course, request.user, request,
                                                include_access=True, include_past_dates=True)

    learner_is_full_access = not ContentTypeGatingConfig.enabled_for_enrollment(request.user, course_key)

    # User locale settings
    user_timezone_locale = user_timezone_locale_prefs(request)
    user_timezone = user_timezone_locale['user_timezone']
    user_language = user_timezone_locale['user_language']

    missed_deadlines, missed_gated_content = dates_banner_should_display(course_key, request.user)

    context = {
        'course': course,
        'course_date_blocks': course_date_blocks,
        'verified_upgrade_link': verified_upgrade_deadline_link(request.user, course=course),
        'learner_is_full_access': learner_is_full_access,
        'user_timezone': user_timezone,
        'user_language': user_language,
        'supports_preview_menu': True,
        'can_masquerade': can_masquerade,
        'masquerade': masquerade,
        'on_dates_tab': True,
        'content_type_gating_enabled': ContentTypeGatingConfig.enabled_for_enrollment(
            user=request.user,
            course_key=course_key,
        ),
        'missed_deadlines': missed_deadlines,
        'missed_gated_content': missed_gated_content,
        'reset_deadlines_url': reverse(RESET_COURSE_DEADLINES_NAME),
        'has_ended': course.has_ended(),
    }

    return render_to_response('courseware/dates.html', context)


@transaction.non_atomic_requests
@login_required
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@ensure_valid_course_key
@data_sharing_consent_required
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

    course = get_course_with_access(request.user, 'load', course_key)

    staff_access = bool(has_access(request.user, 'staff', course))
    can_masquerade = request.user.has_perm(MASQUERADE_AS_STUDENT, course)

    masquerade = None
    if student_id is None or student_id == request.user.id:
        # This will be a no-op for non-staff users, returning request.user
        masquerade, student = setup_masquerade(request, course_key, can_masquerade, reset_masquerade_data=True)
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
    prefetch_related_objects([student], 'groups')
    if request.user.id != student.id:
        # refetch the course as the assumed student
        course = get_course_with_access(student, 'load', course_key, check_if_enrolled=True)

    # NOTE: To make sure impersonation by instructor works, use
    # student instead of request.user in the rest of the function.

    course_grade = CourseGradeFactory().read(student, course)
    courseware_summary = list(course_grade.chapter_grades.values())

    studio_url = get_studio_url(course, 'settings/grading')
    # checking certificate generation configuration
    enrollment_mode, _ = CourseEnrollment.enrollment_mode_for_user(student, course_key)

    course_expiration_fragment = generate_course_expired_fragment(student, course)

    context = {
        'course': course,
        'courseware_summary': courseware_summary,
        'studio_url': studio_url,
        'grade_summary': course_grade.summary,
        'can_masquerade': can_masquerade,
        'staff_access': staff_access,
        'masquerade': masquerade,
        'supports_preview_menu': True,
        'student': student,
        'credit_course_requirements': credit_course_requirements(course_key, student),
        'course_expiration_fragment': course_expiration_fragment,
        'certificate_data': get_cert_data(student, course, enrollment_mode, course_grade)
    }

    context.update(
        get_experiment_user_metadata_context(
            course,
            student,
        )
    )

    with outer_atomic():
        response = render_to_response('courseware/progress.html', context)

    return response


def _downloadable_certificate_message(course, cert_downloadable_status):
    if certs_api.has_html_certificates_enabled(course):
        if certs_api.get_active_web_certificate(course) is not None:
            return _downloadable_cert_data(
                download_url=None,
                cert_web_view_url=certs_api.get_certificate_url(
                    course_id=course.id, uuid=cert_downloadable_status['uuid']
                )
            )
        elif not cert_downloadable_status['is_pdf_certificate']:
            return GENERATING_CERT_DATA

    return _downloadable_cert_data(download_url=cert_downloadable_status['download_url'])


def _missing_required_verification(student, enrollment_mode):
    return (
        enrollment_mode in CourseMode.VERIFIED_MODES and not IDVerificationService.user_is_verified(student)
    )


def _certificate_message(student, course, enrollment_mode):
    if certs_api.is_certificate_invalid(student, course.id):
        return INVALID_CERT_DATA

    cert_downloadable_status = certs_api.certificate_downloadable_status(student, course.id)

    if cert_downloadable_status.get('earned_but_not_available'):
        return EARNED_BUT_NOT_AVAILABLE_CERT_DATA

    if cert_downloadable_status['is_generating']:
        return GENERATING_CERT_DATA

    if cert_downloadable_status['is_unverified']:
        return UNVERIFIED_CERT_DATA

    if cert_downloadable_status['is_downloadable']:
        return _downloadable_certificate_message(course, cert_downloadable_status)

    if _missing_required_verification(student, enrollment_mode):
        return UNVERIFIED_CERT_DATA

    return REQUESTING_CERT_DATA


def get_cert_data(student, course, enrollment_mode, course_grade=None):
    """Returns students course certificate related data.
    Arguments:
        student (User): Student for whom certificate to retrieve.
        course (Course): Course object for which certificate data to retrieve.
        enrollment_mode (String): Course mode in which student is enrolled.
        course_grade (CourseGrade): Student's course grade record.
    Returns:
        returns dict if course certificate is available else None.
    """
    cert_data = _certificate_message(student, course, enrollment_mode)
    if not CourseMode.is_eligible_for_certificate(enrollment_mode, status=cert_data.cert_status):
        return INELIGIBLE_PASSING_CERT_DATA.get(enrollment_mode)

    if cert_data.cert_status == EARNED_BUT_NOT_AVAILABLE_CERT_STATUS:
        return cert_data

    certificates_enabled_for_course = certs_api.cert_generation_enabled(course.id)
    if course_grade is None:
        course_grade = CourseGradeFactory().read(student, course)

    if not auto_certs_api.can_show_certificate_message(course, student, course_grade, certificates_enabled_for_course):
        return

    if not certs_api.get_active_web_certificate(course) and not auto_certs_api.is_valid_pdf_certificate(cert_data):
        return

    return cert_data


def credit_course_requirements(course_key, student):
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


def _course_home_redirect_enabled():
    """
    Return True value if user needs to be redirected to course home based on value of
    `ENABLE_MKTG_SITE` and `ENABLE_COURSE_HOME_REDIRECT feature` flags
    Returns: boolean True or False
    """
    if configuration_helpers.get_value(
            'ENABLE_MKTG_SITE', settings.FEATURES.get('ENABLE_MKTG_SITE', False)
    ) and configuration_helpers.get_value(
        'ENABLE_COURSE_HOME_REDIRECT', settings.FEATURES.get('ENABLE_COURSE_HOME_REDIRECT', True)
    ):
        return True


@login_required
@ensure_valid_course_key
def submission_history(request, course_id, student_username, location):
    """Render an HTML fragment (meant for inclusion elsewhere) that renders a
    history of all state changes made by this user for this problem location.
    Right now this only works for problems because that's all
    StudentModuleHistory records.
    """

    course_key = CourseKey.from_string(course_id)

    try:
        usage_key = UsageKey.from_string(location).map_into_course(course_key)
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
            u"Mismatch when fetching scores for student "
            u"history for course %s, user %s, xblock %s. "
            u"%d scores were found, and %d history entries were found. "
            u"Matching scores to history entries by date for display.",
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
        'course_id': text_type(course_key)
    }

    return render_to_response('courseware/submission_history.html', context)


def get_static_tab_fragment(request, course, tab):
    """
    Returns the fragment for the given static tab
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

    logging.debug(u'course_module = %s', tab_module)

    fragment = Fragment()
    if tab_module is not None:
        try:
            fragment = tab_module.render(STUDENT_VIEW, {})
        except Exception:  # pylint: disable=broad-except
            fragment.content = render_to_string('courseware/error-message.html', None)
            log.exception(
                u"Error rendering course=%s, tab=%s", course, tab['url_slug']
            )

    return fragment


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

    course_key = CourseKey.from_string(course_id)

    try:
        course = get_course(course_key, depth=2)
    except ValueError:
        return HttpResponse(status=404)

    anonymous_user = AnonymousUser()
    anonymous_user.known = False  # make these "noauth" requests like module_render.handle_xblock_callback_noauth
    lti_descriptors = modulestore().get_items(course.id, qualifiers={'category': 'lti'})
    lti_descriptors.extend(modulestore().get_items(course.id, qualifiers={'category': 'lti_consumer'}))

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

    course_key = CourseKey.from_string(course_id)
    course = get_course_with_access(request.user, 'load', course_key, check_survey_complete=False)

    redirect_url = reverse(course_home_url_name(course.id), args=[course_id])

    # if there is no Survey associated with this course,
    # then redirect to the course instead
    if not course.course_survey_name:
        return redirect(redirect_url)

    return survey_views.view_student_survey(
        request.user,
        course.course_survey_name,
        course=course,
        redirect_url=redirect_url,
        is_required=course.course_survey_required,
    )


def is_course_passed(student, course, course_grade=None):
    """
    check user's course passing status. return True if passed
    Arguments:
        student : user object
        course : course object
        course_grade (CourseGrade) : contains student grade details.
    Returns:
        returns bool value
    """
    if course_grade is None:
        course_grade = CourseGradeFactory().read(student, course)
    return course_grade.passed


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

    if not request.user.is_authenticated:
        log.info(u"Anon user trying to generate certificate for %s", course_id)
        return HttpResponseBadRequest(
            _(u'You must be signed in to {platform_name} to create a certificate.').format(
                platform_name=configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME)
            )
        )

    student = request.user
    course_key = CourseKey.from_string(course_id)

    course = modulestore().get_course(course_key, depth=2)
    if not course:
        return HttpResponseBadRequest(_("Course is not valid"))

    if not is_course_passed(student, course):
        log.info(u"User %s has not passed the course: %s", student.username, course_id)
        return HttpResponseBadRequest(_("Your certificate will be available when you pass the course."))

    certificate_status = certs_api.certificate_downloadable_status(student, course.id)

    log.info(
        u"User %s has requested for certificate in %s, current status: is_downloadable: %s, is_generating: %s",
        student.username,
        course_id,
        certificate_status["is_downloadable"],
        certificate_status["is_generating"],
    )

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


def _track_successful_certificate_generation(user_id, course_id):
    """
    Track a successful certificate generation event.
    Arguments:
        user_id (str): The ID of the user generating the certificate.
        course_id (CourseKey): Identifier for the course.
    Returns:
        None
    """
    event_name = 'edx.bi.user.certificate.generate'
    segment.track(user_id, event_name, {
        'category': 'certificates',
        'label': text_type(course_id)
    })


@require_http_methods(["GET", "POST"])
@ensure_valid_usage_key
@xframe_options_exempt
@transaction.non_atomic_requests
@ensure_csrf_cookie
def render_xblock(request, usage_key_string, check_if_enrolled=True):
    """
    Returns an HttpResponse with HTML content for the xBlock with the given usage_key.
    The returned HTML is a chromeless rendering of the xBlock (excluding content of the containing courseware).
    """
    from lms.urls import COURSE_DATES_NAME, RESET_COURSE_DEADLINES_NAME
    from openedx.features.course_experience.urls import COURSE_HOME_VIEW_NAME

    usage_key = UsageKey.from_string(usage_key_string)

    usage_key = usage_key.replace(course_key=modulestore().fill_in_run(usage_key.course_key))
    course_key = usage_key.course_key

    requested_view = request.GET.get('view', 'student_view')
    if requested_view != 'student_view':
        return HttpResponseBadRequest(
            u"Rendering of the xblock view '{}' is not supported.".format(bleach.clean(requested_view, strip=True))
        )

    with modulestore().bulk_operations(course_key):
        # verify the user has access to the course, including enrollment check
        try:
            course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=check_if_enrolled)
        except CourseAccessRedirect:
            raise Http404("Course not found.")

        # get the block, which verifies whether the user has access to the block.
        block, _ = get_module_by_usage_id(
            request, text_type(course_key), text_type(usage_key), disable_staff_debug_info=True, course=course
        )

        student_view_context = request.GET.dict()
        student_view_context['show_bookmark_button'] = request.GET.get('show_bookmark_button', '0') == '1'
        student_view_context['show_title'] = request.GET.get('show_title', '1') == '1'

        enable_completion_on_view_service = False
        completion_service = block.runtime.service(block, 'completion')
        if completion_service and completion_service.completion_tracking_enabled():
            if completion_service.blocks_to_mark_complete_on_view({block}):
                enable_completion_on_view_service = True
                student_view_context['wrap_xblock_data'] = {
                    'mark-completed-on-view-after-delay': completion_service.get_complete_on_view_delay_ms()
                }

        missed_deadlines, missed_gated_content = dates_banner_should_display(course_key, request.user)

        context = {
            'fragment': block.render('student_view', context=student_view_context),
            'course': course,
            'disable_accordion': True,
            'allow_iframing': True,
            'disable_header': True,
            'disable_footer': True,
            'disable_window_wrap': True,
            'enable_completion_on_view_service': enable_completion_on_view_service,
            'edx_notes_enabled': is_feature_enabled(course, request.user),
            'staff_access': bool(request.user.has_perm(VIEW_XQA_INTERFACE, course)),
            'xqa_server': settings.FEATURES.get('XQA_SERVER', 'http://your_xqa_server.com'),
            'missed_deadlines': missed_deadlines,
            'missed_gated_content': missed_gated_content,
            'has_ended': course.has_ended(),
            'web_app_course_url': reverse(COURSE_HOME_VIEW_NAME, args=[course.id]),
            'on_courseware_page': True,
            'verified_upgrade_link': verified_upgrade_deadline_link(request.user, course=course),
            'is_learning_mfe': is_request_from_learning_mfe(request),
            'is_mobile_app': is_request_from_mobile_app(request),
            'reset_deadlines_url': reverse(RESET_COURSE_DEADLINES_NAME),
        }
        return render_to_response('courseware/courseware-chromeless.html', context)


# Translators: "percent_sign" is the symbol "%". "platform_name" is a
# string identifying the name of this installation, such as "edX".
FINANCIAL_ASSISTANCE_HEADER = _(
    u'{platform_name} now offers financial assistance for learners who want to earn Verified Certificates but'
    u' who may not be able to pay the Verified Certificate fee. Eligible learners may receive up to 90{percent_sign} off'
    ' the Verified Certificate fee for a course.\nTo apply for financial assistance, enroll in the'
    ' audit track for a course that offers Verified Certificates, and then complete this application.'
    ' Note that you must complete a separate application for each course you take.\n We plan to use this'
    ' information to evaluate your application for financial assistance and to further develop our'
    ' financial assistance program.'
)


def _get_fa_header(header):
    return header.\
        format(percent_sign="%",
               platform_name=configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME)).split('\n')


FA_INCOME_LABEL = ugettext_noop('Annual Household Income')
FA_REASON_FOR_APPLYING_LABEL = ugettext_noop('Tell us about your current financial situation. Why do you need assistance?')
FA_GOALS_LABEL = ugettext_noop('Tell us about your learning or professional goals. How will a Verified Certificate in this course help you achieve these goals?')

FA_EFFORT_LABEL = ugettext_noop('Tell us about your plans for this course. What steps will you take to help you complete the course work and receive a certificate?')

FA_SHORT_ANSWER_INSTRUCTIONS = _('Use between 1250 and 2500 characters or so in your response.')


@login_required
def financial_assistance(_request):
    """Render the initial financial assistance page."""
    return render_to_response('financial-assistance/financial-assistance.html', {
        'header_text': _get_fa_header(FINANCIAL_ASSISTANCE_HEADER)
    })


@login_required
@require_POST
def financial_assistance_request(request):
    """Submit a request for financial assistance to Zendesk."""
    try:
        data = json.loads(request.body.decode('utf8'))
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
        return HttpResponseBadRequest(u'The field {} is required.'.format(text_type(err)))

    zendesk_submitted = create_zendesk_ticket(
        legal_name,
        email,
        u'Financial assistance request for learner {username} in course {course_name}'.format(
            username=username,
            course_name=course.display_name
        ),
        u'Financial Assistance Request',
        tags={'course_id': course_id},
        # Send the application as additional info on the ticket so
        # that it is not shown when support replies. This uses
        # OrderedDict so that information is presented in the right
        # order.
        additional_info=OrderedDict((
            ('Username', username),
            ('Full Name', legal_name),
            ('Course ID', course_id),
            (FA_INCOME_LABEL, income),
            ('Country', country),
            ('Allowed for marketing purposes', 'Yes' if marketing_permission else 'No'),
            (FA_REASON_FOR_APPLYING_LABEL, '\n' + reason_for_applying + '\n\n'),
            (FA_GOALS_LABEL, '\n' + goals + '\n\n'),
            (FA_EFFORT_LABEL, '\n' + effort + '\n\n'),
            ('Client IP', ip_address),
        )),
        group='Financial Assistance',
    )
    if not (zendesk_submitted == 200 or zendesk_submitted == 201):
        # The call to Zendesk failed. The frontend will display a
        # message to the user.
        return HttpResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return HttpResponse(status=status.HTTP_204_NO_CONTENT)


@login_required
def financial_assistance_form(request):
    """Render the financial assistance application form page."""
    user = request.user
    enrolled_courses = get_financial_aid_courses(user)
    incomes = ['Less than $5,000', '$5,000 - $10,000', '$10,000 - $15,000', '$15,000 - $20,000', '$20,000 - $25,000',
               '$25,000 - $40,000', '$40,000 - $55,000', '$55,000 - $70,000', '$70,000 - $85,000',
               '$85,000 - $100,000', 'More than $100,000']

    annual_incomes = [
        {'name': _(income), 'value': income} for income in incomes
    ]
    return render_to_response('financial-assistance/apply.html', {
        'header_text': _get_fa_header(FINANCIAL_ASSISTANCE_HEADER),
        'student_faq_url': marketing_link('FAQ'),
        'dashboard_url': reverse('dashboard'),
        'account_settings_url': reverse('account_settings'),
        'platform_name': configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME),
        'user_details': {
            'email': user.email,
            'username': user.username,
            'name': user.profile.name,
            'country': text_type(user.profile.country.name),
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
                'instructions': ugettext(
                    'Select the course for which you want to earn a verified certificate. If'
                    ' the course does not appear in the list, make sure that you have enrolled'
                    ' in the audit track for the course.'
                )
            },
            {
                'name': 'income',
                'type': 'select',
                'label': _(FA_INCOME_LABEL),
                'placeholder': '',
                'defaultValue': '',
                'required': True,
                'options': annual_incomes,
                'instructions': _('Specify your annual household income in US Dollars.')
            },
            {
                'name': 'reason_for_applying',
                'type': 'textarea',
                'label': _(FA_REASON_FOR_APPLYING_LABEL),
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
                'label': _(FA_GOALS_LABEL),
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
                'label': _(FA_EFFORT_LABEL),
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


def get_financial_aid_courses(user):
    """ Retrieve the courses eligible for financial assistance. """
    financial_aid_courses = []
    for enrollment in CourseEnrollment.enrollments_for_user(user).order_by('-created'):

        if enrollment.mode != CourseMode.VERIFIED and \
                enrollment.course_overview and \
                enrollment.course_overview.eligible_for_financial_aid and \
                CourseMode.objects.filter(
                    Q(_expiration_datetime__isnull=True) | Q(_expiration_datetime__gt=datetime.now(UTC)),
                    course_id=enrollment.course_id,
                    mode_slug=CourseMode.VERIFIED).exists():

            financial_aid_courses.append(
                {
                    'name': enrollment.course_overview.display_name,
                    'value': text_type(enrollment.course_id)
                }
            )

    return financial_aid_courses
