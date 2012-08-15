from collections import defaultdict
from fs.errors import ResourceNotFoundError
from functools import wraps
import logging

from path import path
from django.conf import settings
from django.http import Http404

from xmodule.course_module import CourseDescriptor
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from static_replace import replace_urls, try_staticfiles_lookup
from courseware.access import has_access

log = logging.getLogger(__name__)


def get_course_by_id(course_id):
    """
    Given a course id, return the corresponding course descriptor.

    If course_id is not valid, raises a 404.
    """
    try:
        course_loc = CourseDescriptor.id_to_location(course_id)
        return modulestore().get_item(course_loc)
    except (KeyError, ItemNotFoundError):
        raise Http404("Course not found.")



def get_course_with_access(user, course_id, action):
    """
    Given a course_id, look up the corresponding course descriptor,
    check that the user has the access to perform the specified action
    on the course, and return the descriptor.

    Raises a 404 if the course_id is invalid, or the user doesn't have access.
    """
    course = get_course_by_id(course_id)
    if not has_access(user, course, action):
        # Deliberately return a non-specific error message to avoid
        # leaking info about access control settings
        raise Http404("Course not found.")
    return course


def get_opt_course_with_access(user, course_id, action):
    """
    Same as get_course_with_access, except that if course_id is None,
    return None without performing any access checks.
    """
    if course_id is None:
        return None
    return get_course_with_access(user, course_id, action)


def course_image_url(course):
    """Try to look up the image url for the course.  If it's not found,
    log an error and return the dead link"""
    path = course.metadata['data_dir'] + "/images/course_image.jpg"
    return try_staticfiles_lookup(path)

def get_course_about_section(course, section_key):
    """
    This returns the snippet of html to be rendered on the course about page,
    given the key for the section.

    Valid keys:
    - overview
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
    """

    # Many of these are stored as html files instead of some semantic
    # markup. This can change without effecting this interface when we find a
    # good format for defining so many snippets of text/html.

# TODO: Remove number, instructors from this list
    if section_key in ['short_description', 'description', 'key_dates', 'video',
                       'course_staff_short', 'course_staff_extended',
                       'requirements', 'syllabus', 'textbook', 'faq', 'more_info',
                       'number', 'instructors', 'overview',
                       'effort', 'end_date', 'prerequisites']:
        try:
            with course.system.resources_fs.open(path("about") / section_key + ".html") as htmlFile:
                return replace_urls(htmlFile.read().decode('utf-8'),
                                    course.metadata['data_dir'])
        except ResourceNotFoundError:
            log.warning("Missing about section {key} in course {url}".format(
                key=section_key, url=course.location.url()))
            return None
    elif section_key == "title":
        return course.metadata.get('display_name', course.url_name)
    elif section_key == "university":
        return course.location.org
    elif section_key == "number":
        return course.number

    raise KeyError("Invalid about key " + str(section_key))


def get_course_info_section(course, section_key):
    """
    This returns the snippet of html to be rendered on the course info page,
    given the key for the section.

    Valid keys:
    - handouts
    - guest_handouts
    - updates
    - guest_updates
    """

    # Many of these are stored as html files instead of some semantic
    # markup. This can change without effecting this interface when we find a
    # good format for defining so many snippets of text/html.

    if section_key in ['handouts', 'guest_handouts', 'updates', 'guest_updates']:
        try:
            with course.system.resources_fs.open(path("info") / section_key + ".html") as htmlFile:
                return replace_urls(htmlFile.read().decode('utf-8'),
                                    course.metadata['data_dir'])
        except ResourceNotFoundError:
            log.exception("Missing info section {key} in course {url}".format(
                key=section_key, url=course.location.url()))
            return "! Info section missing !"

    raise KeyError("Invalid about key " + str(section_key))

def course_staff_group_name(course):
    '''
    course should be either a CourseDescriptor instance, or a string (the
    .course entry of a Location)
    '''
    if isinstance(course, str) or isinstance(course, unicode):
        coursename = course
    else:
        # should be a CourseDescriptor, so grab its location.course:
        coursename = course.location.course
    return 'staff_%s' % coursename

def has_staff_access_to_course(user, course):
    '''
    Returns True if the given user has staff access to the course.
    This means that user is in the staff_* group, or is an overall admin.
    TODO (vshnayder): this needs to be changed to allow per-course_id permissions, not per-course
    (e.g. staff in 2012 is different from 2013, but maybe some people always have access)

    course is the course field of the location being accessed.
    '''
    if user is None or (not user.is_authenticated()) or course is None:
        return False
    if user.is_staff:
        return True

    # note this is the Auth group, not UserTestGroup
    user_groups = [x[1] for x in user.groups.values_list()]
    staff_group = course_staff_group_name(course)
    if staff_group in user_groups:
        return True
    return False

def has_staff_access_to_course_id(user, course_id):
    """Helper method that takes a course_id instead of a course name"""
    loc = CourseDescriptor.id_to_location(course_id)
    return has_staff_access_to_course(user, loc.course)


def has_staff_access_to_location(user, location):
    """Helper method that checks whether the user has staff access to
    the course of the location.

    location: something that can be passed to Location
    """
    return has_staff_access_to_course(user, Location(location).course)

def has_access_to_course(user, course):
    '''course is the .course element of a location'''
    if course.metadata.get('ispublic'):
        return True
    return has_staff_access_to_course(user,course)


def get_courses_by_university(user, domain=None):
    '''
    Returns dict of lists of courses available, keyed by course.org (ie university).
    Courses are sorted by course.number.
    '''
    # TODO: Clean up how 'error' is done.
    # filter out any courses that errored.
    courses = [c for c in modulestore().get_courses()
               if isinstance(c, CourseDescriptor)]
    courses = sorted(courses, key=lambda course: course.number)

    if domain and settings.MITX_FEATURES.get('SUBDOMAIN_COURSE_LISTINGS'):
        subdomain = domain.split(".")[0]
        if subdomain not in settings.COURSE_LISTINGS:
            subdomain = 'default'
        visible_courses = frozenset(settings.COURSE_LISTINGS[subdomain])
    else:
        visible_courses = frozenset(c.id for c in courses)

    universities = defaultdict(list)
    for course in courses:
        if not has_access(user, course, 'see_exists'):
            continue
        if course.id not in visible_courses:
            continue
        universities[course.org].append(course)
    return universities

