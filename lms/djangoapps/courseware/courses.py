from collections import defaultdict
from fs.errors import ResourceNotFoundError
from functools import wraps
import logging
import inspect

from lxml.html import rewrite_links

from path import path
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import Http404

from module_render import get_module
from xmodule.course_module import CourseDescriptor
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.content import StaticContent
from xmodule.modulestore.xml import XMLModuleStore
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.x_module import XModule
from static_replace import replace_urls, try_staticfiles_lookup
from courseware.access import has_access
import branding
from courseware.models import StudentModuleCache

log = logging.getLogger(__name__)

def get_request_for_thread():
    """Walk up the stack, return the nearest first argument named "request"."""
    frame = None
    try:
        for f in inspect.stack()[1:]:
            frame = f[0]
            code = frame.f_code
            if code.co_varnames[:1] == ("request",):
                return frame.f_locals["request"]
            elif code.co_varnames[:2] == ("self", "request",):
                return frame.f_locals["request"]
    finally:
        del frame


def get_course_by_id(course_id):
    """
    Given a course id, return the corresponding course descriptor.

    If course_id is not valid, raises a 404.
    """
    try:
        course_loc = CourseDescriptor.id_to_location(course_id)
        return modulestore().get_instance(course_id, course_loc)
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
    if isinstance(modulestore(), XMLModuleStore):
        path = course.metadata['data_dir'] + "/images/course_image.jpg"
        return try_staticfiles_lookup(path)
    else:
        loc = course.location._replace(tag='c4x', category='asset', name='images_course_image.jpg')
        path = StaticContent.get_url_path_from_location(loc)
        return path

def find_file(fs, dirs, filename):
    """
    Looks for a filename in a list of dirs on a filesystem, in the specified order.

    fs: an OSFS filesystem
    dirs: a list of path objects
    filename: a string

    Returns d / filename if found in dir d, else raises ResourceNotFoundError.
    """
    for d in dirs:
        filepath = path(d) / filename
        if fs.exists(filepath):
            return filepath
    raise ResourceNotFoundError("Could not find {0}".format(filename))

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
    - ocw_links
    """

    # Many of these are stored as html files instead of some semantic
    # markup. This can change without effecting this interface when we find a
    # good format for defining so many snippets of text/html.

# TODO: Remove number, instructors from this list
    if section_key in ['short_description', 'description', 'key_dates', 'video',
                       'course_staff_short', 'course_staff_extended',
                       'requirements', 'syllabus', 'textbook', 'faq', 'more_info',
                       'number', 'instructors', 'overview',
                       'effort', 'end_date', 'prerequisites', 'ocw_links']:

        try:

            request = get_request_for_thread()

            student_module_cache = StudentModuleCache.cache_for_descriptor_descendents(
                course.id, request.user, course, depth=2)

            loc = course.location._replace(category='about', name=section_key)
            course_module = get_module(request.user, request, loc, student_module_cache, course.id)

            html = ''

            if course_module is not None:
                html = course_module.get_html()

            return html

        except ItemNotFoundError:
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



def get_course_info_section(request, cache, course, section_key):
    """
    This returns the snippet of html to be rendered on the course info page,
    given the key for the section.

    Valid keys:
    - handouts
    - guest_handouts
    - updates
    - guest_updates
    """


    loc = Location(course.location.tag, course.location.org, course.location.course, 'course_info', section_key)
    course_module = get_module(request.user, request, loc, cache, course.id)

    html = ''

    if course_module is not None:
        html = course_module.get_html()

    return html



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
            fs = course.system.resources_fs
            # first look for a run-specific version
            dirs = [path("syllabus") / course.url_name, path("syllabus")]
            filepath = find_file(fs, dirs, section_key + ".html")
            with fs.open(filepath) as htmlFile:
                return replace_urls(htmlFile.read().decode('utf-8'),
                                    course.metadata['data_dir'])
        except ResourceNotFoundError:
            log.exception("Missing syllabus section {key} in course {url}".format(
                key=section_key, url=course.location.url()))
            return "! Syllabus missing !"

    raise KeyError("Invalid about key " + str(section_key))


def get_courses_by_university(user, domain=None):
    '''
    Returns dict of lists of courses available, keyed by course.org (ie university).
    Courses are sorted by course.number.
    '''
    # TODO: Clean up how 'error' is done.
    # filter out any courses that errored.
    visible_courses = branding.get_visible_courses(domain)

    universities = defaultdict(list)
    for course in visible_courses:
        if not has_access(user, course, 'see_exists'):
            continue
        universities[course.org].append(course)
    return universities
