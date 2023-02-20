"""
Functions for accessing and displaying courses within the
courseware.
"""

import logging
from collections import defaultdict, namedtuple
from datetime import datetime

import six
import pytz
from crum import get_current_request
from dateutil.parser import parse as parse_date
from django.conf import settings
from django.http import Http404, QueryDict
from django.urls import reverse
from django.utils.translation import gettext as _
from edx_django_utils.monitoring import function_trace
from fs.errors import ResourceNotFound
from opaque_keys.edx.keys import UsageKey
from path import Path as path

from common.djangoapps.edxmako.shortcuts import render_to_string
from common.djangoapps.static_replace import replace_static_urls
from common.djangoapps.util.date_utils import strftime_localized
from lms.djangoapps import branding
from lms.djangoapps.course_blocks.api import get_course_blocks
from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.courseware.access_response import (
    AuthenticationRequiredAccessError,
    EnrollmentRequiredAccessError,
    MilestoneAccessError,
    OldMongoAccessError,
    StartDateError
)
from lms.djangoapps.courseware.access_utils import check_authentication, check_data_sharing_consent, check_enrollment, \
    check_correct_active_enterprise_customer, is_priority_access_error
from lms.djangoapps.courseware.courseware_access_exception import CoursewareAccessException
from lms.djangoapps.courseware.date_summary import (
    CertificateAvailableDate,
    CourseAssignmentDate,
    CourseEndDate,
    CourseExpiredDate,
    CourseStartDate,
    TodaysDate,
    VerificationDeadlineDate,
    VerifiedUpgradeDeadlineDate
)
from lms.djangoapps.courseware.exceptions import CourseAccessRedirect, CourseRunNotFound
from lms.djangoapps.courseware.masquerade import check_content_start_date_for_masquerade_user
from lms.djangoapps.courseware.model_data import FieldDataCache
from lms.djangoapps.courseware.block_render import get_block
from lms.djangoapps.survey.utils import SurveyRequiredAccessError, check_survey_required_and_unanswered
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.enrollments.api import get_course_enrollment_details
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.lib.api.view_utils import LazySequence
from openedx.core.lib.cache_utils import request_cached
from openedx.core.lib.courses import get_course_by_id
from openedx.features.course_duration_limits.access import AuditExpiredError
from openedx.features.course_experience import RELATIVE_DATES_FLAG
from openedx.features.course_experience.utils import is_block_structure_complete_for_assignments
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.exceptions import ItemNotFoundError  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.x_module import STUDENT_VIEW  # lint-amnesty, pylint: disable=wrong-import-order

log = logging.getLogger(__name__)


# Used by get_course_assignments below. You shouldn't need to use this type directly.
_Assignment = namedtuple(
    'Assignment', ['block_key', 'title', 'url', 'date', 'contains_gated_content', 'complete', 'past_due',
                   'assignment_type', 'extra_info', 'first_component_block_id']
)


def get_course(course_id, depth=0):
    """
    Given a course id, return the corresponding course descriptor.

    If the course does not exist, raises a CourseRunNotFound. This is appropriate
    for internal use.

    depth: The number of levels of children for the modulestore to cache.
    None means infinite depth.  Default is to fetch no children.
    """
    course = modulestore().get_course(course_id, depth=depth)
    if course is None:
        raise CourseRunNotFound(course_key=course_id)
    return course


def get_course_with_access(user, action, course_key, depth=0, check_if_enrolled=False, check_survey_complete=True, check_if_authenticated=False):  # lint-amnesty, pylint: disable=line-too-long
    """
    Given a course_key, look up the corresponding course descriptor,
    check that the user has the access to perform the specified action
    on the course, and return the descriptor.

    Raises a 404 if the course_key is invalid, or the user doesn't have access.

    depth: The number of levels of children for the modulestore to cache. None means infinite depth

    check_if_enrolled: If true, additionally verifies that the user is either enrolled in the course
      or has staff access.
    check_survey_complete: If true, additionally verifies that the user has either completed the course survey
      or has staff access.
      Note: We do not want to continually add these optional booleans.  Ideally,
      these special cases could not only be handled inside has_access, but could
      be plugged in as additional callback checks for different actions.
    """
    course = get_course_by_id(course_key, depth)
    check_course_access_with_redirect(course, user, action, check_if_enrolled, check_survey_complete, check_if_authenticated)  # lint-amnesty, pylint: disable=line-too-long
    return course


def get_course_overview_with_access(user, action, course_key, check_if_enrolled=False):
    """
    Given a course_key, look up the corresponding course overview,
    check that the user has the access to perform the specified action
    on the course, and return the course overview.

    Raises a 404 if the course_key is invalid, or the user doesn't have access.

    check_if_enrolled: If true, additionally verifies that the user is either enrolled in the course
      or has staff access.
    """
    try:
        course_overview = CourseOverview.get_from_id(course_key)
    except CourseOverview.DoesNotExist:
        raise Http404("Course not found.")  # lint-amnesty, pylint: disable=raise-missing-from
    check_course_access_with_redirect(course_overview, user, action, check_if_enrolled)
    return course_overview


def check_course_access(
    course,
    user,
    action,
    check_if_enrolled=False,
    check_survey_complete=True,
    check_if_authenticated=False,
    apply_enterprise_checks=False,
):
    """
    Check that the user has the access to perform the specified action
    on the course (CourseBlock|CourseOverview).

    check_if_enrolled: If true, additionally verifies that the user is enrolled.
    check_survey_complete: If true, additionally verifies that the user has completed the survey.
    """
    def _check_nonstaff_access():
        # Below is a series of checks that must all pass for a user to be granted access
        # to a course. (Essentially check this AND check that AND...)
        # Also note: access_response (AccessResponse) objects are compared as booleans
        access_response = has_access(user, action, course, course.id)
        if not access_response:
            return access_response

        if check_if_authenticated:
            authentication_access_response = check_authentication(user, course)
            if not authentication_access_response:
                return authentication_access_response

        if check_if_enrolled:
            enrollment_access_response = check_enrollment(user, course)
            if not enrollment_access_response:
                return enrollment_access_response

        if apply_enterprise_checks:
            correct_active_enterprise_response = check_correct_active_enterprise_customer(user, course.id)
            if not correct_active_enterprise_response:
                return correct_active_enterprise_response

            data_sharing_consent_response = check_data_sharing_consent(course.id)
            if not data_sharing_consent_response:
                return data_sharing_consent_response

        # Redirect if the user must answer a survey before entering the course.
        if check_survey_complete and action == 'load':
            survey_access_response = check_survey_required_and_unanswered(user, course)
            if not survey_access_response:
                return survey_access_response

        # This access_response will be ACCESS_GRANTED
        return access_response

    non_staff_access_response = _check_nonstaff_access()

    # User has course access OR access error is a priority error
    if non_staff_access_response or is_priority_access_error(non_staff_access_response):
        return non_staff_access_response

    # Allow staff full access to the course even if other checks fail
    staff_access_response = has_access(user, 'staff', course.id)
    if staff_access_response:
        return staff_access_response

    return non_staff_access_response


def check_course_access_with_redirect(course, user, action, check_if_enrolled=False, check_survey_complete=True, check_if_authenticated=False):  # lint-amnesty, pylint: disable=line-too-long
    """
    Check that the user has the access to perform the specified action
    on the course (CourseBlock|CourseOverview).

    check_if_enrolled: If true, additionally verifies that the user is enrolled.
    check_survey_complete: If true, additionally verifies that the user has completed the survey.
    """
    request = get_current_request()
    check_content_start_date_for_masquerade_user(course.id, user, request, course.start)

    access_response = check_course_access(course, user, action, check_if_enrolled, check_survey_complete, check_if_authenticated)  # lint-amnesty, pylint: disable=line-too-long

    if not access_response:
        # Redirect if StartDateError
        if isinstance(access_response, StartDateError):
            start_date = strftime_localized(course.start, 'SHORT_DATE')
            params = QueryDict(mutable=True)
            params['notlive'] = start_date
            raise CourseAccessRedirect('{dashboard_url}?{params}'.format(
                dashboard_url=reverse('dashboard'),
                params=params.urlencode()
            ), access_response)

        # Redirect if AuditExpiredError
        if isinstance(access_response, AuditExpiredError):
            params = QueryDict(mutable=True)
            params['access_response_error'] = access_response.additional_context_user_message
            raise CourseAccessRedirect('{dashboard_url}?{params}'.format(
                dashboard_url=reverse('dashboard'),
                params=params.urlencode()
            ), access_response)

        # Redirect if trying to access an Old Mongo course
        if isinstance(access_response, OldMongoAccessError):
            params = QueryDict(mutable=True)
            params['access_response_error'] = access_response.user_message
            raise CourseAccessRedirect('{dashboard_url}?{params}'.format(
                dashboard_url=reverse('dashboard'),
                params=params.urlencode(),
            ), access_response)

        # Redirect if the user must answer a survey before entering the course.
        if isinstance(access_response, MilestoneAccessError):
            raise CourseAccessRedirect('{dashboard_url}'.format(
                dashboard_url=reverse('dashboard'),
            ), access_response)

        # Redirect if the user is not enrolled and must be to see content
        if isinstance(access_response, EnrollmentRequiredAccessError):
            raise CourseAccessRedirect(reverse('about_course', args=[str(course.id)]))

        # Redirect if user must be authenticated to view the content
        if isinstance(access_response, AuthenticationRequiredAccessError):
            raise CourseAccessRedirect(reverse('about_course', args=[str(course.id)]))

        # Redirect if the user must answer a survey before entering the course.
        if isinstance(access_response, SurveyRequiredAccessError):
            raise CourseAccessRedirect(reverse('course_survey', args=[str(course.id)]))

        # Deliberately return a non-specific error message to avoid
        # leaking info about access control settings
        raise CoursewareAccessException(access_response)


def can_self_enroll_in_course(course_key):
    """
    Returns True if the user can enroll themselves in a course.

    Note: an example of a course that a user cannot enroll in directly
    is a CCX course. For such courses, a user can only be enrolled by
    a CCX coach.
    """
    if hasattr(course_key, 'ccx'):
        return False
    return True


def course_open_for_self_enrollment(course_key):
    """
    For a given course_key, determine if the course is available for enrollment
    """
    # Check to see if learners can enroll themselves.
    if not can_self_enroll_in_course(course_key):
        return False

    # Check the enrollment start and end dates.
    course_details = get_course_enrollment_details(str(course_key))
    now = datetime.now().replace(tzinfo=pytz.UTC)
    start = course_details['enrollment_start']
    end = course_details['enrollment_end']

    start = start if start is not None else now
    end = end if end is not None else now

    # If we are not within the start and end date for enrollment.
    if now < start or end < now:
        return False

    return True


def find_file(filesystem, dirs, filename):
    """
    Looks for a filename in a list of dirs on a filesystem, in the specified order.

    filesystem: an OSFS filesystem
    dirs: a list of path objects
    filename: a string

    Returns d / filename if found in dir d, else raises ResourceNotFound.
    """
    for directory in dirs:
        filepath = path(directory) / filename
        if filesystem.exists(filepath):
            return filepath
    raise ResourceNotFound(f"Could not find {filename}")


def get_course_about_section(request, course, section_key):
    """
    This returns the snippet of html to be rendered on the course about page,
    given the key for the section.

    Valid keys:
    - overview
    - about_sidebar_html
    - short_description
    - description
    - key_dates (includes start, end, exams, etc)
    - video
    - course_staff_short
    - course_staff_extended
    - requirements
    - syllabus
    - textbook
    - faq
    - effort
    - more_info
    - ocw_links
    """

    # Many of these are stored as html files instead of some semantic
    # markup. This can change without effecting this interface when we find a
    # good format for defining so many snippets of text/html.

    html_sections = {
        'short_description',
        'description',
        'key_dates',
        'video',
        'course_staff_short',
        'course_staff_extended',
        'requirements',
        'syllabus',
        'textbook',
        'faq',
        'more_info',
        'overview',
        'effort',
        'end_date',
        'prerequisites',
        'about_sidebar_html',
        'ocw_links'
    }

    if section_key in html_sections:
        try:
            loc = course.location.replace(category='about', name=section_key)

            # Use an empty cache
            field_data_cache = FieldDataCache([], course.id, request.user)
            about_block = get_block(
                request.user,
                request,
                loc,
                field_data_cache,
                log_if_not_found=False,
                wrap_xblock_display=False,
                static_asset_path=course.static_asset_path,
                course=course
            )

            html = ''

            if about_block is not None:
                try:
                    html = about_block.render(STUDENT_VIEW).content
                except Exception:  # pylint: disable=broad-except
                    html = render_to_string('courseware/error-message.html', None)
                    log.exception(
                        "Error rendering course=%s, section_key=%s",
                        course, section_key
                    )
            return html

        except ItemNotFoundError:
            log.warning(
                "Missing about section %s in course %s",
                section_key, str(course.location)
            )
            return None

    raise KeyError("Invalid about key " + str(section_key))


def get_course_info_usage_key(course, section_key):
    """
    Returns the usage key for the specified section's course info block.
    """
    return course.id.make_usage_key('course_info', section_key)


def get_course_info_section_block(request, user, course, section_key):
    """
    This returns the course info block for a given section_key.

    Valid keys:
    - handouts
    - guest_handouts
    - updates
    - guest_updates
    """
    usage_key = get_course_info_usage_key(course, section_key)

    # Use an empty cache
    field_data_cache = FieldDataCache([], course.id, user)

    return get_block(
        user,
        request,
        usage_key,
        field_data_cache,
        log_if_not_found=False,
        wrap_xblock_display=False,
        static_asset_path=course.static_asset_path,
        course=course
    )


def get_course_info_section(request, user, course, section_key):
    """
    This returns the snippet of html to be rendered on the course info page,
    given the key for the section.

    Valid keys:
    - handouts
    - guest_handouts
    - updates
    - guest_updates
    """
    info_block = get_course_info_section_block(request, user, course, section_key)

    html = ''
    if info_block is not None:
        try:
            html = info_block.render(STUDENT_VIEW).content.strip()
        except Exception:  # pylint: disable=broad-except
            html = render_to_string('courseware/error-message.html', None)
            log.exception(
                "Error rendering course_id=%s, section_key=%s",
                str(course.id), section_key
            )

    return html


def get_course_date_blocks(course, user, request=None, include_access=False,
                           include_past_dates=False, num_assignments=None):
    """
    Return the list of blocks to display on the course info page,
    sorted by date.
    """
    blocks = []
    if RELATIVE_DATES_FLAG.is_enabled(course.id):
        blocks.extend(get_course_assignment_date_blocks(
            course, user, request, num_return=num_assignments,
            include_access=include_access, include_past_dates=include_past_dates,
        ))

    # Adding these in after the assignment blocks so in the case multiple blocks have the same date,
    # these blocks will be sorted to come after the assignments. See https://openedx.atlassian.net/browse/AA-158
    default_block_classes = [
        CertificateAvailableDate,
        CourseEndDate,
        CourseExpiredDate,
        CourseStartDate,
        TodaysDate,
        VerificationDeadlineDate,
        VerifiedUpgradeDeadlineDate,
    ]
    blocks.extend([cls(course, user) for cls in default_block_classes])

    blocks = filter(lambda b: b.is_allowed and b.date and (include_past_dates or b.is_enabled), blocks)
    return sorted(blocks, key=date_block_key_fn)


def date_block_key_fn(block):
    """
    If the block's date is None, return the maximum datetime in order
    to force it to the end of the list of displayed blocks.
    """
    return block.date or datetime.max.replace(tzinfo=pytz.UTC)


def _get_absolute_url(request, url_path):
    """Construct an absolute URL back to the site.

    Arguments:
        request (request): request object.
        url_path (string): The path of the URL.

    Returns:
        URL

    """
    if not url_path:
        return ''

    if request:
        return request.build_absolute_uri(url_path)

    site_name = configuration_helpers.get_value('SITE_NAME', settings.SITE_NAME)
    parts = ("https" if settings.HTTPS == "on" else "http", site_name, url_path, '', '', '')
    return six.moves.urllib.parse.urlunparse(parts)


def get_course_assignment_date_blocks(course, user, request, num_return=None,
                                      include_past_dates=False, include_access=False):
    """
    Returns a list of assignment (at the subsection/sequential level) due date
    blocks for the given course. Will return num_return results or all results
    if num_return is None in date increasing order.
    """
    date_blocks = []
    for assignment in get_course_assignments(course.id, user, include_access=include_access):
        date_block = CourseAssignmentDate(course, user)
        date_block.date = assignment.date
        date_block.contains_gated_content = assignment.contains_gated_content
        date_block.first_component_block_id = assignment.first_component_block_id
        date_block.complete = assignment.complete
        date_block.assignment_type = assignment.assignment_type
        date_block.past_due = assignment.past_due
        date_block.link = _get_absolute_url(request, assignment.url)
        date_block.set_title(assignment.title, link=assignment.url)
        date_block._extra_info = assignment.extra_info  # pylint: disable=protected-access
        date_blocks.append(date_block)
    date_blocks = sorted((b for b in date_blocks if b.is_enabled or include_past_dates), key=date_block_key_fn)
    if num_return:
        return date_blocks[:num_return]
    return date_blocks


@request_cached()
def get_course_blocks_completion_summary(course_key, user):
    """
    Returns an object with the number of complete units, incomplete units, and units that contain gated content
    for the given course. The complete and incomplete counts only reflect units that are able to be completed by
    the given user. If a unit contains gated content, it is not counted towards the incomplete count.

    The object contains fields: complete_count, incomplete_count, locked_count
    """
    if not user.id:
        return []
    store = modulestore()
    course_usage_key = store.make_course_usage_key(course_key)
    block_data = get_course_blocks(user, course_usage_key, allow_start_dates_in_future=True, include_completion=True)

    complete_count, incomplete_count, locked_count = 0, 0, 0
    for section_key in block_data.get_children(course_usage_key):  # pylint: disable=too-many-nested-blocks
        for subsection_key in block_data.get_children(section_key):
            for unit_key in block_data.get_children(subsection_key):
                complete = block_data.get_xblock_field(unit_key, 'complete', False)
                contains_gated_content = block_data.get_xblock_field(unit_key, 'contains_gated_content', False)
                if contains_gated_content:
                    locked_count += 1
                elif complete:
                    complete_count += 1
                else:
                    incomplete_count += 1

    return {
        'complete_count': complete_count,
        'incomplete_count': incomplete_count,
        'locked_count': locked_count
    }


@request_cached()
def get_course_assignments(course_key, user, include_access=False):  # lint-amnesty, pylint: disable=too-many-statements
    """
    Returns a list of assignment (at the subsection/sequential level) due dates for the given course.

    Each returned object is a namedtuple with fields: title, url, date, contains_gated_content, complete, past_due,
    assignment_type
    """
    if not user.id:
        return []

    store = modulestore()
    course_usage_key = store.make_course_usage_key(course_key)
    block_data = get_course_blocks(user, course_usage_key, allow_start_dates_in_future=True, include_completion=True)

    now = datetime.now(pytz.UTC)
    assignments = []
    for section_key in block_data.get_children(course_usage_key):  # lint-amnesty, pylint: disable=too-many-nested-blocks
        for subsection_key in block_data.get_children(section_key):
            due = block_data.get_xblock_field(subsection_key, 'due')
            graded = block_data.get_xblock_field(subsection_key, 'graded', False)
            if due and graded:
                first_component_block_id = get_first_component_of_block(subsection_key, block_data)
                contains_gated_content = include_access and block_data.get_xblock_field(
                    subsection_key, 'contains_gated_content', False)
                title = block_data.get_xblock_field(subsection_key, 'display_name', _('Assignment'))

                assignment_type = block_data.get_xblock_field(subsection_key, 'format', None)

                url = None
                start = block_data.get_xblock_field(subsection_key, 'start')
                assignment_released = not start or start < now
                if assignment_released:
                    url = reverse('jump_to', args=[course_key, subsection_key])
                    complete = is_block_structure_complete_for_assignments(block_data, subsection_key)
                else:
                    complete = False

                past_due = not complete and due < now
                assignments.append(_Assignment(
                    subsection_key, title, url, due, contains_gated_content,
                    complete, past_due, assignment_type, None, first_component_block_id
                ))

            # Load all dates for ORA blocks as separate assignments
            descendents = block_data.get_children(subsection_key)
            while descendents:
                descendent = descendents.pop()
                descendents.extend(block_data.get_children(descendent))
                if block_data.get_xblock_field(descendent, 'category', None) == 'openassessment':
                    graded = block_data.get_xblock_field(descendent, 'graded', False)
                    has_score = block_data.get_xblock_field(descendent, 'has_score', False)
                    weight = block_data.get_xblock_field(descendent, 'weight', 1)
                    if not (graded and has_score and (weight is None or weight > 0)):
                        continue

                    all_assessments = [{
                        'name': 'submission',
                        'due': block_data.get_xblock_field(descendent, 'submission_due'),
                        'start': block_data.get_xblock_field(descendent, 'submission_start'),
                        'required': True
                    }]

                    valid_assessments = block_data.get_xblock_field(descendent, 'valid_assessments')
                    if valid_assessments:
                        all_assessments.extend(valid_assessments)

                    assignment_type = block_data.get_xblock_field(descendent, 'format', None)
                    complete = is_block_structure_complete_for_assignments(block_data, descendent)

                    block_title = block_data.get_xblock_field(descendent, 'title', _('Open Response Assessment'))

                    for assessment in all_assessments:
                        due = parse_date(assessment.get('due')).replace(tzinfo=pytz.UTC) if assessment.get('due') else None  # lint-amnesty, pylint: disable=line-too-long
                        if due is None:
                            continue

                        assessment_name = assessment.get('name')
                        if assessment_name is None:
                            continue

                        if assessment_name == 'self-assessment':
                            assessment_type = _("Self Assessment")
                        elif assessment_name == 'peer-assessment':
                            assessment_type = _("Peer Assessment")
                        elif assessment_name == 'staff-assessment':
                            assessment_type = _("Staff Assessment")
                        elif assessment_name == 'submission':
                            assessment_type = _("Submission")
                        else:
                            assessment_type = assessment_name
                        title = f"{block_title} ({assessment_type})"
                        url = ''
                        start = parse_date(assessment.get('start')).replace(tzinfo=pytz.UTC) if assessment.get('start') else None  # lint-amnesty, pylint: disable=line-too-long
                        assignment_released = not start or start < now
                        if assignment_released:
                            url = reverse('jump_to', args=[course_key, descendent])

                        past_due = not complete and due and due < now
                        first_component_block_id = str(descendent)
                        assignments.append(_Assignment(
                            descendent,
                            title,
                            url,
                            due,
                            False,
                            complete,
                            past_due,
                            assignment_type,
                            _("Open Response Assessment due dates are set by your instructor and can't be shifted."),
                            first_component_block_id,
                        ))
    return assignments


def get_first_component_of_block(block_key, block_data):
    """
    This function returns the first leaf block of a section(block_key)
    """
    descendents = block_data.get_children(block_key)
    if descendents:
        return get_first_component_of_block(descendents[0], block_data)

    return str(block_key)


# TODO: Fix this such that these are pulled in as extra course-specific tabs.
#       arjun will address this by the end of October if no one does so prior to
#       then.
def get_course_syllabus_section(course, section_key):
    """
    This returns the snippet of html to be rendered on the syllabus page,
    given the key for the section.

    Valid keys:
    - syllabus
    - guest_syllabus
    """

    # Many of these are stored as html files instead of some semantic
    # markup. This can change without effecting this interface when we find a
    # good format for defining so many snippets of text/html.

    if section_key in ['syllabus', 'guest_syllabus']:
        try:
            filesys = course.runtime.resources_fs
            # first look for a run-specific version
            dirs = [path("syllabus") / course.url_name, path("syllabus")]
            filepath = find_file(filesys, dirs, section_key + ".html")
            with filesys.open(filepath) as html_file:
                return replace_static_urls(
                    html_file.read().decode('utf-8'),
                    getattr(course, 'data_dir', None),
                    course_id=course.id,
                    static_asset_path=course.static_asset_path,
                )
        except ResourceNotFound:
            log.exception(
                "Missing syllabus section %s in course %s",
                section_key, str(course.location)
            )
            return "! Syllabus missing !"

    raise KeyError("Invalid about key " + str(section_key))


@function_trace('get_courses')
def get_courses(user, org=None, filter_=None, permissions=None, active_only=False):
    """
    Return a LazySequence of courses available, optionally filtered by org code
    (case-insensitive) or a set of permissions to be satisfied for the specified
    user.
    """

    courses = branding.get_visible_courses(
        org=org,
        filter_=filter_,
        active_only=active_only
    ).prefetch_related(
        'modes',
    ).select_related(
        'image_set'
    )

    permissions = set(permissions or '')
    permission_name = configuration_helpers.get_value(
        'COURSE_CATALOG_VISIBILITY_PERMISSION',
        settings.COURSE_CATALOG_VISIBILITY_PERMISSION
    )
    permissions.add(permission_name)

    return LazySequence(
        (c for c in courses if all(has_access(user, p, c) for p in permissions)),
        est_len=courses.count()
    )


def get_permission_for_course_about():
    """
    Returns the CourseOverview object for the course after checking for access.
    """
    return configuration_helpers.get_value(
        'COURSE_ABOUT_VISIBILITY_PERMISSION',
        settings.COURSE_ABOUT_VISIBILITY_PERMISSION
    )


def sort_by_announcement(courses):
    """
    Sorts a list of courses by their announcement date. If the date is
    not available, sort them by their start date.
    """

    # Sort courses by how far are they from they start day
    def _key(course):
        return course.sorting_score
    courses = sorted(courses, key=_key)

    return courses


def sort_by_start_date(courses):
    """
    Returns a list of courses sorted by their start date, latest first.
    """
    courses = sorted(
        courses,
        key=lambda course: (course.has_ended(), course.start is None, course.start),
        reverse=False
    )

    return courses


def get_cms_course_link(course, page='course'):
    """
    Returns a link to course_index for editing the course in cms,
    assuming that the course is actually cms-backed.
    """
    # This is fragile, but unfortunately the problem is that within the LMS we
    # can't use the reverse calls from the CMS
    return f"//{settings.CMS_BASE}/{page}/{str(course.id)}"


def get_cms_block_link(block, page):
    """
    Returns a link to block_index for editing the course in cms,
    assuming that the block is actually cms-backed.
    """
    # This is fragile, but unfortunately the problem is that within the LMS we
    # can't use the reverse calls from the CMS
    return f"//{settings.CMS_BASE}/{page}/{block.location}"


def get_studio_url(course, page):
    """
    Get the Studio URL of the page that is passed in.

    Args:
        course (CourseBlock)
    """
    studio_link = None
    if course.course_edit_method == "Studio":
        studio_link = get_cms_course_link(course, page)
    return studio_link


def get_problems_in_section(section):
    """
    This returns a dict having problems in a section.
    Returning dict has problem location as keys and problem
    descriptor as values.
    """

    problem_descriptors = defaultdict()
    if not isinstance(section, UsageKey):
        section_key = UsageKey.from_string(section)
    else:
        section_key = section
    # it will be a Mongo performance boost, if you pass in a depth=3 argument here
    # as it will optimize round trips to the database to fetch all children for the current node
    section_descriptor = modulestore().get_item(section_key, depth=3)

    # iterate over section, sub-section, vertical
    for subsection in section_descriptor.get_children():
        for vertical in subsection.get_children():
            for component in vertical.get_children():
                if component.location.block_type == 'problem' and getattr(component, 'has_score', False):
                    problem_descriptors[str(component.location)] = component

    return problem_descriptors


def get_current_child(xblock, min_depth=None, requested_child=None):
    """
    Get the xblock.position's display item of an xblock that has a position and
    children.  If xblock has no position or is out of bounds, return the first
    child with children of min_depth.

    For example, if chapter_one has no position set, with two child sections,
    section-A having no children and section-B having a discussion unit,
    `get_current_child(chapter, min_depth=1)`  will return section-B.

    Returns None only if there are no children at all.
    """
    # TODO: convert this method to use the Course Blocks API
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

    def _get_default_child_block(child_blocks):
        """Returns the first child of xblock, subject to min_depth."""
        if min_depth is None or min_depth <= 0:
            return _get_child(child_blocks)
        else:
            content_children = [
                child for child in child_blocks
                if child.has_children_at_depth(min_depth - 1) and child.get_children()
            ]
            return _get_child(content_children) if content_children else None

    child = None

    try:
        # In python 3, hasattr() catches AttributeErrors only then returns False.
        # All other exceptions bubble up the call stack.
        has_position = hasattr(xblock, 'position')  # This conditions returns AssertionError from xblock.fields lib.
    except AssertionError:
        return child

    if has_position:
        children = xblock.get_children()
        if len(children) > 0:
            if xblock.position is not None and not requested_child:
                pos = int(xblock.position) - 1  # position is 1-indexed
                if 0 <= pos < len(children):
                    child = children[pos]
                    if min_depth is not None and (min_depth > 0 and not child.has_children_at_depth(min_depth - 1)):
                        child = None
            if child is None:
                child = _get_default_child_block(children)

    return child


def get_course_chapter_ids(course_key):
    """
    Extracts the chapter block keys from a course structure.

    Arguments:
        course_key (CourseLocator): The course key
    Returns:
        list (string): The list of string representations of the chapter block keys in the course.
    """
    try:
        chapter_keys = modulestore().get_course(course_key).children
    except Exception:  # pylint: disable=broad-except
        log.exception('Failed to retrieve course from modulestore.')
        return []
    return [str(chapter_key) for chapter_key in chapter_keys if chapter_key.block_type == 'chapter']
