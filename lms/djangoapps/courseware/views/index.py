"""
View for Courseware Index
"""

# pylint: disable=attribute-defined-outside-init


import logging

import six
from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.db import transaction
from django.http import Http404
from django.template.context_processors import csrf
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import View
from edx_django_utils.monitoring import set_custom_attributes_for_course_key
from edx_toggles.toggles import WaffleSwitchNamespace
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey
from six.moves import urllib
from web_fragments.fragment import Fragment

from common.djangoapps.edxmako.shortcuts import render_to_response, render_to_string
from lms.djangoapps.courseware.exceptions import CourseAccessRedirect, Redirect
from lms.djangoapps.experiments.utils import get_experiment_user_metadata_context
from lms.djangoapps.gating.api import get_entrance_exam_score_ratio, get_entrance_exam_usage_key
from lms.djangoapps.grades.api import CourseGradeFactory
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.crawlers.models import CrawlersConfig
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.user_api.preferences.api import get_user_preference
from openedx.core.djangoapps.util.user_messages import PageLevelMessages
from openedx.core.djangolib.markup import HTML, Text
from openedx.features.course_experience import (
    COURSE_ENABLE_UNENROLLED_ACCESS_FLAG,
    DISABLE_COURSE_OUTLINE_PAGE_FLAG,
    RELATIVE_DATES_FLAG,
    default_course_url_name
)
from openedx.features.course_experience.urls import COURSE_HOME_VIEW_NAME
from openedx.features.course_experience.views.course_sock import CourseSockFragmentView
from openedx.features.enterprise_support.api import data_sharing_consent_required
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.util.views import ensure_valid_course_key
from xmodule.course_module import COURSE_VISIBILITY_PUBLIC
from xmodule.modulestore.django import modulestore
from xmodule.x_module import PUBLIC_VIEW, STUDENT_VIEW

from ..access import has_access
from ..access_utils import check_public_access
from ..courses import check_course_access_with_redirect, get_course_with_access, get_current_child, get_studio_url
from ..entrance_exams import (
    course_has_entrance_exam,
    get_entrance_exam_content,
    user_can_skip_entrance_exam,
    user_has_passed_entrance_exam
)
from ..masquerade import check_content_start_date_for_masquerade_user, setup_masquerade
from ..model_data import FieldDataCache
from ..module_render import get_module_for_descriptor, toc_for_course
from ..permissions import MASQUERADE_AS_STUDENT
from ..toggles import COURSEWARE_MICROFRONTEND_COURSE_TEAM_PREVIEW, REDIRECT_TO_COURSEWARE_MICROFRONTEND
from ..url_helpers import get_microfrontend_url
from .views import CourseTabView

log = logging.getLogger("edx.courseware.views.index")

TEMPLATE_IMPORTS = {'urllib': urllib}
CONTENT_DEPTH = 2


@method_decorator(transaction.non_atomic_requests, name='dispatch')
class CoursewareIndex(View):
    """
    View class for the Courseware page.
    """

    @cached_property
    def enable_unenrolled_access(self):
        return COURSE_ENABLE_UNENROLLED_ACCESS_FLAG.is_enabled(self.course_key)

    @method_decorator(ensure_csrf_cookie)
    @method_decorator(cache_control(no_cache=True, no_store=True, must_revalidate=True))
    @method_decorator(ensure_valid_course_key)
    @method_decorator(data_sharing_consent_required)
    def get(self, request, course_id, chapter=None, section=None, position=None):
        """
        Displays courseware accordion and associated content.  If course, chapter,
        and section are all specified, renders the page, or returns an error if they
        are invalid.

        If section is not specified, displays the accordion opened to the right
        chapter.

        If neither chapter or section are specified, displays the user's most
        recent chapter, or the first chapter if this is the user's first visit.

        Arguments:
            request: HTTP request
            course_id (unicode): course id
            chapter (unicode): chapter url_name
            section (unicode): section url_name
            position (unicode): position in module, eg of <sequential> module
        """
        self.course_key = CourseKey.from_string(course_id)

        if not (request.user.is_authenticated or self.enable_unenrolled_access):
            return redirect_to_login(request.get_full_path())

        self.original_chapter_url_name = chapter
        self.original_section_url_name = section
        self.chapter_url_name = chapter
        self.section_url_name = section
        self.position = position
        self.chapter, self.section = None, None
        self.course = None
        self.url = request.path

        try:
            set_custom_attributes_for_course_key(self.course_key)
            self._clean_position()
            with modulestore().bulk_operations(self.course_key):

                self.view = STUDENT_VIEW

                self.course = get_course_with_access(
                    request.user, 'load', self.course_key,
                    depth=CONTENT_DEPTH,
                    check_if_enrolled=True,
                    check_if_authenticated=True
                )
                self.course_overview = CourseOverview.get_from_id(self.course.id)
                self.is_staff = has_access(request.user, 'staff', self.course)

                # There's only one situation where we want to show the public view
                if (
                        not self.is_staff and
                        self.enable_unenrolled_access and
                        self.course.course_visibility == COURSE_VISIBILITY_PUBLIC and
                        not CourseEnrollment.is_enrolled(request.user, self.course_key)
                ):
                    self.view = PUBLIC_VIEW

                self.can_masquerade = request.user.has_perm(MASQUERADE_AS_STUDENT, self.course)
                self._setup_masquerade_for_effective_user()

                return self.render(request)
        except Exception as exception:  # pylint: disable=broad-except
            return CourseTabView.handle_exceptions(request, self.course_key, self.course, exception)

    def _setup_masquerade_for_effective_user(self):
        """
        Setup the masquerade information to allow the request to
        be processed for the requested effective user.
        """
        self.real_user = self.request.user
        self.masquerade, self.effective_user = setup_masquerade(
            self.request,
            self.course_key,
            self.can_masquerade,
            reset_masquerade_data=True
        )
        # Set the user in the request to the effective user.
        self.request.user = self.effective_user

    def _redirect_to_learning_mfe(self):
        """
        Redirect to the new courseware micro frontend,
        unless this is a time limited exam.
        """
        # DENY: feature disabled globally
        if not settings.FEATURES.get('ENABLE_COURSEWARE_MICROFRONTEND'):
            return
        # DENY: staff access
        if self.is_staff:
            return
        # DENY: Old Mongo courses, until removed from platform
        if self.course_key.deprecated:
            return
        # DENY: Timed Exams, until supported
        if getattr(self.section, 'is_time_limited', False):
            return
        # ALLOW: when flag set for course
        if REDIRECT_TO_COURSEWARE_MICROFRONTEND.is_enabled(self.course_key):
            raise Redirect(self.microfrontend_url)

    @property
    def microfrontend_url(self):
        """
        Return absolute URL to this section in the courseware micro-frontend.
        """
        try:
            unit_key = UsageKey.from_string(self.request.GET.get('activate_block_id', ''))
            # `activate_block_id` is typically a Unit (a.k.a. Vertical),
            # but it can technically be any block type. Do a check to
            # make sure it's really a Unit before we use it for the MFE.
            if unit_key.block_type != 'vertical':
                unit_key = None
        except InvalidKeyError:
            unit_key = None
        url = get_microfrontend_url(
            self.course_key,
            self.section.location if self.section else None,
            unit_key
        )
        return url

    def render(self, request):
        """
        Render the index page.
        """
        self._prefetch_and_bind_course(request)

        if self.course.has_children_at_depth(CONTENT_DEPTH):
            self._reset_section_to_exam_if_required()
            self.chapter = self._find_chapter()
            self.section = self._find_section()

            if self.chapter and self.section:
                self._redirect_if_not_requested_section()
                self._save_positions()
                self._prefetch_and_bind_section()
                self._redirect_to_learning_mfe()

            check_content_start_date_for_masquerade_user(self.course_key, self.effective_user, request,
                                                         self.course.start, self.chapter.start, self.section.start)

        if not request.user.is_authenticated:
            qs = six.moves.urllib.parse.urlencode({
                'course_id': self.course_key,
                'enrollment_action': 'enroll',
                'email_opt_in': False,
            })

            allow_anonymous = check_public_access(self.course, [COURSE_VISIBILITY_PUBLIC])

            if not allow_anonymous:
                PageLevelMessages.register_warning_message(
                    request,
                    Text(_(u"You are not signed in. To see additional course content, {sign_in_link} or "
                           u"{register_link}, and enroll in this course.")).format(
                        sign_in_link=HTML(u'<a href="{url}">{sign_in_label}</a>').format(
                            sign_in_label=_('sign in'),
                            url='{}?{}'.format(reverse('signin_user'), qs),
                        ),
                        register_link=HTML(u'<a href="/{url}">{register_label}</a>').format(
                            register_label=_('register'),
                            url=u'{}?{}'.format(reverse('register_user'), qs),
                        ),
                    )
                )

        return render_to_response('courseware/courseware.html', self._create_courseware_context(request))

    def _redirect_if_not_requested_section(self):
        """
        If the resulting section and chapter are different from what was initially
        requested, redirect back to the index page, but with an updated URL that includes
        the correct section and chapter values.  We do this so that our analytics events
        and error logs have the appropriate URLs.
        """
        if (
                self.chapter.url_name != self.original_chapter_url_name or
                (self.original_section_url_name and self.section.url_name != self.original_section_url_name)
        ):
            raise CourseAccessRedirect(
                reverse(
                    'courseware_section',
                    kwargs={
                        'course_id': six.text_type(self.course_key),
                        'chapter': self.chapter.url_name,
                        'section': self.section.url_name,
                    },
                )
            )

    def _clean_position(self):
        """
        Verify that the given position is an integer. If it is not positive, set it to 1.
        """
        if self.position is not None:
            try:
                self.position = max(int(self.position), 1)
            except ValueError:
                raise Http404(u"Position {} is not an integer!".format(self.position))

    def _reset_section_to_exam_if_required(self):
        """
        Check to see if an Entrance Exam is required for the user.
        """
        if not user_can_skip_entrance_exam(self.effective_user, self.course):
            exam_chapter = get_entrance_exam_content(self.effective_user, self.course)
            if exam_chapter and exam_chapter.get_children():
                exam_section = exam_chapter.get_children()[0]
                if exam_section:
                    self.chapter_url_name = exam_chapter.url_name
                    self.section_url_name = exam_section.url_name

    def _get_language_preference(self):
        """
        Returns the preferred language for the actual user making the request.
        """
        language_preference = settings.LANGUAGE_CODE

        if self.request.user.is_authenticated:
            language_preference = get_user_preference(self.real_user, LANGUAGE_KEY)

        return language_preference

    def _is_masquerading_as_student(self):
        """
        Returns whether the current request is masquerading as a student.
        """
        return self.masquerade and self.masquerade.role == 'student'

    def _is_masquerading_as_specific_student(self):
        """
        Returns whether the current request is masqueurading as a specific student.
        """
        return self._is_masquerading_as_student() and self.masquerade.user_name

    def _find_block(self, parent, url_name, block_type, min_depth=None):
        """
        Finds the block in the parent with the specified url_name.
        If not found, calls get_current_child on the parent.
        """
        child = None
        if url_name:
            child = parent.get_child_by(lambda m: m.location.block_id == url_name)
            if not child:
                # User may be trying to access a child that isn't live yet
                if not self._is_masquerading_as_student():
                    raise Http404(u'No {block_type} found with name {url_name}'.format(
                        block_type=block_type,
                        url_name=url_name,
                    ))
            elif min_depth and not child.has_children_at_depth(min_depth - 1):
                child = None
        if not child:
            child = get_current_child(parent, min_depth=min_depth, requested_child=self.request.GET.get("child"))
        return child

    def _find_chapter(self):
        """
        Finds the requested chapter.
        """
        return self._find_block(self.course, self.chapter_url_name, 'chapter', CONTENT_DEPTH - 1)

    def _find_section(self):
        """
        Finds the requested section.
        """
        if self.chapter:
            return self._find_block(self.chapter, self.section_url_name, 'section')

    def _prefetch_and_bind_course(self, request):
        """
        Prefetches all descendant data for the requested section and
        sets up the runtime, which binds the request user to the section.
        """
        self.field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.course_key,
            self.effective_user,
            self.course,
            depth=CONTENT_DEPTH,
            read_only=CrawlersConfig.is_crawler(request),
        )

        self.course = get_module_for_descriptor(
            self.effective_user,
            self.request,
            self.course,
            self.field_data_cache,
            self.course_key,
            course=self.course,
            will_recheck_access=True,
        )

    def _prefetch_and_bind_section(self):
        """
        Prefetches all descendant data for the requested section and
        sets up the runtime, which binds the request user to the section.
        """
        # Pre-fetch all descendant data
        self.section = modulestore().get_item(self.section.location, depth=None, lazy=False)
        self.field_data_cache.add_descriptor_descendents(self.section, depth=None)

        # Bind section to user
        self.section = get_module_for_descriptor(
            self.effective_user,
            self.request,
            self.section,
            self.field_data_cache,
            self.course_key,
            self.position,
            course=self.course,
            will_recheck_access=True,
        )

    def _save_positions(self):
        """
        Save where we are in the course and chapter.
        """
        save_child_position(self.course, self.chapter_url_name)
        save_child_position(self.chapter, self.section_url_name)

    def _create_courseware_context(self, request):
        """
        Returns and creates the rendering context for the courseware.
        Also returns the table of contents for the courseware.
        """

        course_url_name = default_course_url_name(self.course.id)
        course_url = reverse(course_url_name, kwargs={'course_id': six.text_type(self.course.id)})
        show_search = (
            settings.FEATURES.get('ENABLE_COURSEWARE_SEARCH') or
            (settings.FEATURES.get('ENABLE_COURSEWARE_SEARCH_FOR_COURSE_STAFF') and self.is_staff)
        )
        staff_access = self.is_staff

        courseware_context = {
            'csrf': csrf(self.request)['csrf_token'],
            'course': self.course,
            'course_url': course_url,
            'chapter': self.chapter,
            'section': self.section,
            'init': '',
            'fragment': Fragment(),
            'staff_access': staff_access,
            'can_masquerade': self.can_masquerade,
            'masquerade': self.masquerade,
            'supports_preview_menu': True,
            'studio_url': get_studio_url(self.course, 'course'),
            'xqa_server': settings.FEATURES.get('XQA_SERVER', "http://your_xqa_server.com"),
            'bookmarks_api_url': reverse('bookmarks'),
            'language_preference': self._get_language_preference(),
            'disable_optimizely': not WaffleSwitchNamespace('RET').is_enabled('enable_optimizely_in_courseware'),
            'section_title': None,
            'sequence_title': None,
            'disable_accordion': not DISABLE_COURSE_OUTLINE_PAGE_FLAG.is_enabled(self.course.id),
            'show_search': show_search,
        }
        courseware_context.update(
            get_experiment_user_metadata_context(
                self.course,
                self.effective_user,
            )
        )
        table_of_contents = toc_for_course(
            self.effective_user,
            self.request,
            self.course,
            self.chapter_url_name,
            self.section_url_name,
            self.field_data_cache,
        )
        courseware_context['accordion'] = render_accordion(
            self.request,
            self.course,
            table_of_contents['chapters'],
        )

        courseware_context['course_sock_fragment'] = CourseSockFragmentView().render_to_fragment(
            request, course=self.course)

        # entrance exam data
        self._add_entrance_exam_to_context(courseware_context)

        if self.section:
            # chromeless data
            if self.section.chrome:
                chrome = [s.strip() for s in self.section.chrome.lower().split(",")]
                if 'accordion' not in chrome:
                    courseware_context['disable_accordion'] = True
                if 'tabs' not in chrome:
                    courseware_context['disable_tabs'] = True

            # default tab
            if self.section.default_tab:
                courseware_context['default_tab'] = self.section.default_tab

            # section data
            courseware_context['section_title'] = self.section.display_name_with_default
            section_context = self._create_section_context(
                table_of_contents['previous_of_active_section'],
                table_of_contents['next_of_active_section'],
            )
            courseware_context['fragment'] = self.section.render(self.view, section_context)

            if self.section.position and self.section.has_children:
                self._add_sequence_title_to_context(courseware_context)

        # Courseware MFE link
        if show_courseware_mfe_link(request.user, staff_access, self.course.id):
            courseware_context['microfrontend_link'] = self.microfrontend_url
        else:
            courseware_context['microfrontend_link'] = None

        return courseware_context

    def _add_sequence_title_to_context(self, courseware_context):
        """
        Adds sequence title to the given context.

        If we're rendering a section with some display items, but position
        exceeds the length of the displayable items, default the position
        to the first element.
        """
        display_items = self.section.get_display_items()
        if not display_items:
            return
        if self.section.position > len(display_items):
            self.section.position = 1
        courseware_context['sequence_title'] = display_items[self.section.position - 1].display_name_with_default

    def _add_entrance_exam_to_context(self, courseware_context):
        """
        Adds entrance exam related information to the given context.
        """
        if course_has_entrance_exam(self.course) and getattr(self.chapter, 'is_entrance_exam', False):
            courseware_context['entrance_exam_passed'] = user_has_passed_entrance_exam(self.effective_user, self.course)
            courseware_context['entrance_exam_current_score'] = get_entrance_exam_score_ratio(
                CourseGradeFactory().read(self.effective_user, self.course),
                get_entrance_exam_usage_key(self.course),
            )

    def _create_section_context(self, previous_of_active_section, next_of_active_section):
        """
        Returns and creates the rendering context for the section.
        """
        def _compute_section_url(section_info, requested_child):
            """
            Returns the section URL for the given section_info with the given child parameter.
            """
            return "{url}?child={requested_child}".format(
                url=reverse(
                    'courseware_section',
                    args=[six.text_type(self.course_key), section_info['chapter_url_name'], section_info['url_name']],
                ),
                requested_child=requested_child,
            )

        # NOTE (CCB): Pull the position from the URL for un-authenticated users. Otherwise, pull the saved
        # state from the data store.
        position = None if self.request.user.is_authenticated else self.position
        section_context = {
            'activate_block_id': self.request.GET.get('activate_block_id'),
            'requested_child': self.request.GET.get("child"),
            'progress_url': reverse('progress', kwargs={'course_id': six.text_type(self.course_key)}),
            'user_authenticated': self.request.user.is_authenticated,
            'position': position,
        }
        if previous_of_active_section:
            section_context['prev_url'] = _compute_section_url(previous_of_active_section, 'last')
        if next_of_active_section:
            section_context['next_url'] = _compute_section_url(next_of_active_section, 'first')
        # sections can hide data that masquerading staff should see when debugging issues with specific students
        section_context['specific_masquerade'] = self._is_masquerading_as_specific_student()
        return section_context


def render_accordion(request, course, table_of_contents):
    """
    Returns the HTML that renders the navigation for the given course.
    Expects the table_of_contents to have data on each chapter and section,
    including which ones are active.
    """
    context = dict(
        [
            ('toc', table_of_contents),
            ('course_id', six.text_type(course.id)),
            ('csrf', csrf(request)['csrf_token']),
            ('due_date_display_format', course.due_date_display_format),
        ] + list(TEMPLATE_IMPORTS.items())
    )
    return render_to_string('courseware/accordion.html', context)


def save_child_position(seq_module, child_name):
    """
    child_name: url_name of the child
    """
    for position, child in enumerate(seq_module.get_display_items(), start=1):
        if child.location.block_id == child_name:
            # Only save if position changed
            if position != seq_module.position:
                seq_module.position = position
    # Save this new position to the underlying KeyValueStore
    seq_module.save()


def save_positions_recursively_up(user, request, field_data_cache, xmodule, course=None):
    """
    Recurses up the course tree starting from a leaf
    Saving the position property based on the previous node as it goes
    """
    current_module = xmodule

    while current_module:
        parent_location = modulestore().get_parent_location(current_module.location)
        parent = None
        if parent_location:
            parent_descriptor = modulestore().get_item(parent_location)
            parent = get_module_for_descriptor(
                user,
                request,
                parent_descriptor,
                field_data_cache,
                current_module.location.course_key,
                course=course
            )

        if parent and hasattr(parent, 'position'):
            save_child_position(parent, current_module.location.block_id)

        current_module = parent


def show_courseware_mfe_link(user, staff_access, course_key):
    """
    Return whether to display the button to switch to the Courseware MFE.
    """
    # The MFE isn't enabled at all, so don't show the button.
    if not settings.FEATURES.get('ENABLE_COURSEWARE_MICROFRONTEND'):
        return False

    # MFE does not work for Old Mongo courses.
    if course_key.deprecated:
        return False

    # Global staff members always get to see the courseware MFE button if the
    # platform and course are capable, regardless of rollout waffle flags.
    if user.is_staff:
        return True

    # If you have course staff access, you see this link if we've enabled the
    # course team preview CourseWaffleFlag for this course *or* if we've turned
    # on the redirect for your students.
    mfe_enabled_for_course_team = COURSEWARE_MICROFRONTEND_COURSE_TEAM_PREVIEW.is_enabled(course_key)
    mfe_experiment_enabled_for_course = REDIRECT_TO_COURSEWARE_MICROFRONTEND.is_experiment_on(course_key)

    if staff_access and (mfe_enabled_for_course_team or mfe_experiment_enabled_for_course):
        return True

    return False
