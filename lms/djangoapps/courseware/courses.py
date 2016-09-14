"""
Functions for accessing and displaying courses within the
courseware.
"""
from datetime import datetime
from collections import defaultdict
from fs.errors import ResourceNotFoundError
import logging
import inspect

from path import Path as path
import pytz
from django.http import Http404
from django.conf import settings

from edxmako.shortcuts import render_to_string
from xmodule.modulestore import ModuleStoreEnum
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.content import StaticContent
from xmodule.modulestore.exceptions import ItemNotFoundError
from static_replace import replace_static_urls
from xmodule.modulestore import ModuleStoreEnum
from xmodule.x_module import STUDENT_VIEW
from microsite_configuration import microsite
from util.date_utils import get_default_time_display
from util.keyword_substitution import substitute_keywords_with_data

from courseware.access import has_access
from courseware.date_summary import (
    CourseEndDate,
    CourseStartDate,
    TodaysDate,
    VerificationDeadlineDate,
    VerifiedUpgradeDeadlineDate,
)
from courseware.model_data import FieldDataCache
from courseware.module_render import get_module
from lms.djangoapps.courseware.courseware_access_exception import CoursewareAccessException
from student.models import CourseEnrollment
import branding
from student.models import CourseEnrollment

from opaque_keys.edx.keys import UsageKey


log = logging.getLogger(__name__)


def get_course(course_id, depth=0):
    """
    Given a course id, return the corresponding course descriptor.

    If the course does not exist, raises a ValueError.  This is appropriate
    for internal use.

    depth: The number of levels of children for the modulestore to cache.
    None means infinite depth.  Default is to fetch no children.
    """
    course = modulestore().get_course(course_id, depth=depth)
    if course is None:
        raise ValueError(u"Course not found: {0}".format(course_id))
    return course


# TODO please rename this function to get_course_by_key at next opportunity!
def get_course_by_id(course_key, depth=0):
    """
    Given a course id, return the corresponding course descriptor.

    If such a course does not exist, raises a 404.

    depth: The number of levels of children for the modulestore to cache. None means infinite depth
    """
    with modulestore().bulk_operations(course_key):
        course = modulestore().get_course(course_key, depth=depth)
    if course:
        return course
    else:
        raise Http404("Course not found.")


class UserNotEnrolled(Http404):
    def __init__(self, course_key):
        super(UserNotEnrolled, self).__init__()
        self.course_key = course_key


def get_course_with_access(user, action, course_key, depth=0, check_if_enrolled=False):
    """
    Given a course_key, look up the corresponding course descriptor,
    check that the user has the access to perform the specified action
    on the course, and return the descriptor.

    Raises a 404 if the course_key is invalid, or the user doesn't have access.

    depth: The number of levels of children for the modulestore to cache. None means infinite depth

    check_if_enrolled: If true, additionally verifies that the user is either enrolled in the course
      or has staff access.
    """
    assert isinstance(course_key, CourseKey)
    course = get_course_by_id(course_key, depth=depth)
    access_response = has_access(user, action, course, course_key)

    if not access_response:
        # Deliberately return a non-specific error message to avoid
        # leaking info about access control settings
        raise CoursewareAccessException(access_response)

    if check_if_enrolled:
        # Verify that the user is either enrolled in the course or a staff member.
        # If user is not enrolled, raise UserNotEnrolled exception that will be caught by middleware.
        if not ((user.id and CourseEnrollment.is_enrolled(user, course_key)) or has_access(user, 'staff', course)):
            raise UserNotEnrolled(course_key)

    return course


def course_image_url(course):
    """Try to look up the image url for the course.  If it's not found,
    log an error and return the dead link"""
    if course.static_asset_path or modulestore().get_modulestore_type(course.id) == ModuleStoreEnum.Type.xml:
        # If we are a static course with the course_image attribute
        # set different than the default, return that path so that
        # courses can use custom course image paths, otherwise just
        # return the default static path.
        url = '/static/' + (course.static_asset_path or getattr(course, 'data_dir', ''))
        if hasattr(course, 'course_image') and course.course_image != course.fields['course_image'].default:
            url += '/' + course.course_image
        else:
            url += '/images/course_image.jpg'
    elif not course.course_image:
        # if course_image is empty, use the default image url from settings
        url = settings.STATIC_URL + settings.DEFAULT_COURSE_ABOUT_IMAGE_URL
    else:
        loc = StaticContent.compute_location(course.id, course.course_image)
        url = StaticContent.serialize_asset_key_with_slash(loc)
    return url


def find_file(filesystem, dirs, filename):
    """
    Looks for a filename in a list of dirs on a filesystem, in the specified order.

    filesystem: an OSFS filesystem
    dirs: a list of path objects
    filename: a string

    Returns d / filename if found in dir d, else raises ResourceNotFoundError.
    """
    for directory in dirs:
        filepath = path(directory) / filename
        if filesystem.exists(filepath):
            return filepath
    raise ResourceNotFoundError(u"Could not find {0}".format(filename))


def get_course_university_about_section(course):  # pylint: disable=invalid-name
    """
    Returns a snippet of HTML displaying the course's university.

    Arguments:
        course (CourseDescriptor|CourseOverview): A course.
    """
    return course.display_org_with_default


def get_course_about_section(request, course, section_key):
    """
    This returns the snippet of html to be rendered on the course about page,
    given the key for the section.

    Valid keys:
    - overview
    - about_sidebar_html
    - title
    - university
    - number
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
    - more_info
    - ocw_links
    - pre_enrollment_email
    - post_enrollment_email
    - pre_enrollment_email_subject
    - post_enrollment_email_subject
    """

    # Many of these are stored as html files instead of some semantic
    # markup. This can change without effecting this interface when we find a
    # good format for defining so many snippets of text/html.

    # TODO: Remove number, instructors from this set
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
        'number',
        'instructors',
        'overview',
        'effort',
        'end_date',
        'prerequisites',
        'ocw_links',
        'about_sidebar_html',
        'pre_enrollment_email',
        'post_enrollment_email',
        'pre_enrollment_email_subject',
        'post_enrollment_email_subject',
    }

    if section_key in html_sections:
        try:
            loc = course.location.replace(category='about', name=section_key)

            # Use an empty cache
            field_data_cache = FieldDataCache([], course.id, request.user)
            about_module = get_module(
                request.user,
                request,
                loc,
                field_data_cache,
                log_if_not_found=False,
                wrap_xmodule_display=False,
                static_asset_path=course.static_asset_path,
                course=course
            )

            html = ''

            if about_module is not None:
                try:
                    html = about_module.render(STUDENT_VIEW).content
                except Exception:  # pylint: disable=broad-except
                    html = render_to_string('courseware/error-message.html', None)
                    log.exception(
                        u"Error rendering course=%s, section_key=%s",
                        course, section_key
                    )
            return html

        except ItemNotFoundError:
            log.warning(
                u"Missing about section %s in course %s",
                section_key, course.location.to_deprecated_string()
            )
            return None
    elif section_key == "title":
        return course.display_name_with_default
    elif section_key == "university":
        return get_course_university_about_section(course)
    elif section_key == "number":
        return course.display_number_with_default

    raise KeyError("Invalid about key " + str(section_key))


def get_course_info_section_module(request, course, section_key):
    """
    This returns the course info module for a given section_key.

    Valid keys:
    - handouts
    - guest_handouts
    - updates
    - guest_updates
    """
    usage_key = course.id.make_usage_key('course_info', section_key)

    # Use an empty cache
    field_data_cache = FieldDataCache([], course.id, request.user)

    return get_module(
        request.user,
        request,
        usage_key,
        field_data_cache,
        log_if_not_found=False,
        wrap_xmodule_display=False,
        static_asset_path=course.static_asset_path,
        course=course
    )


def get_course_info_section(request, course, section_key):
    """
    This returns the snippet of html to be rendered on the course info page,
    given the key for the section.

    Valid keys:
    - handouts
    - guest_handouts
    - updates
    - guest_updates
    """
    info_module = get_course_info_section_module(request, course, section_key)

    html = ''
    if info_module is not None:
        try:
            html = info_module.render(STUDENT_VIEW).content
            context = {
                'username': request.user.username,
                'user_id': request.user.id,
                'name': request.user.profile.name,
                'course_title': course.display_name,
                'course_id': course.id,
                'course_start_date': get_default_time_display(course.start),
                'course_end_date': get_default_time_display(course.end),
            }
            html = substitute_keywords_with_data(html, context)
        except Exception:  # pylint: disable=broad-except
            html = render_to_string('courseware/error-message.html', None)
            log.exception(
                u"Error rendering course=%s, section_key=%s",
                course, section_key
            )

    return html


def get_course_date_summary(course, user):
    """
    Return the snippet of HTML to be included on the course info page
    in the 'Date Summary' section.
    """
    blocks = _get_course_date_summary_blocks(course, user)
    return '\n'.join(
        b.render() for b in blocks
    )


def _get_course_date_summary_blocks(course, user):
    """
    Return the list of blocks to display on the course info page,
    sorted by date.
    """
    block_classes = (
        CourseEndDate,
        CourseStartDate,
        TodaysDate,
        VerificationDeadlineDate,
        VerifiedUpgradeDeadlineDate,
    )

    blocks = (cls(course, user) for cls in block_classes)

    def block_key_fn(block):
        """
        If the block's date is None, return the maximum datetime in order
        to force it to the end of the list of displayed blocks.
        """
        if block.date is None:
            return datetime.max.replace(tzinfo=pytz.UTC)
        return block.date
    return sorted((b for b in blocks if b.is_enabled), key=block_key_fn)


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
            filesys = course.system.resources_fs
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
        except ResourceNotFoundError:
            log.exception(
                u"Missing syllabus section %s in course %s",
                section_key, course.location.to_deprecated_string()
            )
            return "! Syllabus missing !"

    raise KeyError("Invalid about key " + str(section_key))


def get_courses_by_university(user, domain=None):
    '''
    Returns dict of lists of courses available, keyed by course.org (ie university).
    Courses are sorted by course.number.
    '''
    # TODO: Clean up how 'error' is done.
    # filter out any courses that errored.
    visible_courses = get_courses(user, domain)

    universities = defaultdict(list)
    for course in visible_courses:
        universities[course.org].append(course)

    return universities


def get_courses(user, domain=None):
    '''
    Returns a list of courses available, sorted by course.number
    '''
    courses = branding.get_visible_courses()

    permission_name = microsite.get_value(
        'COURSE_CATALOG_VISIBILITY_PERMISSION',
        settings.COURSE_CATALOG_VISIBILITY_PERMISSION
    )

    courses = [c for c in courses if has_access(user, permission_name, c)]

    courses = sorted(courses, key=lambda course: course.number)

    return courses


def sort_by_announcement(courses):
    """
    Sorts a list of courses by their announcement date. If the date is
    not available, sort them by their start date.
    """

    # Sort courses by how far are they from they start day
    key = lambda course: course.sorting_score
    courses = sorted(courses, key=key)

    return courses


def registered_for_course(course, user):
    """
    Return CourseEnrollment if user is registered for course, else False
    """
    if user is None:
        return False
    if user.is_authenticated():
        return CourseEnrollment.is_enrolled(user, course.id)
    else:
        return False


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
    return u"//{}/{}/{}".format(settings.CMS_BASE, page, unicode(course.id))


def get_cms_block_link(block, page):
    """
    Returns a link to block_index for editing the course in cms,
    assuming that the block is actually cms-backed.
    """
    # This is fragile, but unfortunately the problem is that within the LMS we
    # can't use the reverse calls from the CMS
    return u"//{}/{}/{}".format(settings.CMS_BASE, page, block.location)


def get_studio_url(course, page):
    """
    Get the Studio URL of the page that is passed in.

    Args:
        course (CourseDescriptor)
    """
    is_studio_course = course.course_edit_method == "Studio"
    is_mongo_course = modulestore().get_modulestore_type(course.id) != ModuleStoreEnum.Type.xml
    studio_link = None
    if is_studio_course and is_mongo_course:
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
                if component.location.category == 'problem' and getattr(component, 'has_score', False):
                    problem_descriptors[unicode(component.location)] = component

    return problem_descriptors
