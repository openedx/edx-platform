__author__ = 'sina'


from student.roles import GlobalStaff, UserBasedRole, CourseInstructorRole, CourseStaffRole
from xmodule.error_module import ErrorDescriptor
from student.auth import has_studio_read_access, has_studio_write_access
from xmodule.modulestore.django import modulestore
from course_action_state.models import CourseRerunState, CourseRerunUIStateManager
from xmodule.modulestore.exceptions import ItemNotFoundError
from contentstore.utils import reverse_course_url, get_lms_link_for_item, reverse_library_url


class AccessListFallback(Exception):
    """
    An exception that is raised whenever we need to `fall back` to fetching *all* courses
    available to a user, rather than using a shorter method (i.e. fetching by group)
    """
    pass


def get_courses_accessible_to_user(request, this_user=None):
    """
    Try to get all courses by first reversing django groups and fallback to old method if it fails
    Note: overhead of pymongo reads will increase if getting courses from django groups fails
    """
    if this_user:
        user = this_user
    else:
        user = request.user

    if GlobalStaff().has_user(user):
        # user has global access so no need to get courses from django groups
        courses, in_process_course_actions = _accessible_courses_list(request, user)
    else:
        try:
            courses, in_process_course_actions = _accessible_courses_list_from_groups(request, user)
        except AccessListFallback:
            # user have some old groups or there was some error getting courses from django groups
            # so fallback to iterating through all courses
            courses, in_process_course_actions = _accessible_courses_list(request, user)
    return courses, in_process_course_actions


def _accessible_courses_list(request, this_user=None):
    """
    List all courses available to the logged in user by iterating through all the courses
    """
    if this_user:
        user = this_user
    else:
        user = request.user

    def course_filter(course):
        """
        Filter out unusable and inaccessible courses
        """
        if isinstance(course, ErrorDescriptor):
            return False

        # pylint: disable=fixme
        # TODO remove this condition when templates purged from db
        if course.location.course == 'templates':
            return False

        return has_studio_read_access(user, course.id)

    courses = filter(course_filter, modulestore().get_courses())
    in_process_course_actions = [
        course for course in
        CourseRerunState.objects.find_all(
            exclude_args={'state': CourseRerunUIStateManager.State.SUCCEEDED}, should_display=True
        )
        if has_studio_read_access(user, course.course_key)
    ]
    return courses, in_process_course_actions


def _accessible_courses_list_from_groups(request, this_user=None):
    """
    List all courses available to the logged in user by reversing access group names
    """
    if this_user:
        user = this_user
    else:
        user = request.user

    courses_list = {}
    in_process_course_actions = []

    instructor_courses = UserBasedRole(user, CourseInstructorRole.ROLE).courses_with_role()
    staff_courses = UserBasedRole(user, CourseStaffRole.ROLE).courses_with_role()
    all_courses = instructor_courses | staff_courses

    for course_access in all_courses:
        course_key = course_access.course_id
        if course_key is None:
            # If the course_access does not have a course_id, it's an org-based role, so we fall back
            raise AccessListFallback
        if course_key not in courses_list:
            # check for any course action state for this course
            in_process_course_actions.extend(
                CourseRerunState.objects.find_all(
                    exclude_args={'state': CourseRerunUIStateManager.State.SUCCEEDED},
                    should_display=True,
                    course_key=course_key,
                )
            )
            # check for the course itself
            try:
                course = modulestore().get_course(course_key)
            except ItemNotFoundError:
                # If a user has access to a course that doesn't exist, don't do anything with that course
                pass
            if course is not None and not isinstance(course, ErrorDescriptor):
                # ignore deleted or errored courses
                courses_list[course_key] = course

    return courses_list.values(), in_process_course_actions


def accessible_libraries_list(user):
    """
    List all libraries available to the logged in user by iterating through all libraries
    """
    # No need to worry about ErrorDescriptors - split's get_libraries() never returns them.
    return [lib for lib in modulestore().get_libraries() if has_studio_read_access(user, lib.location.library_key)]


def format_course_for_view(course):
    """
    Return a dict of the data which the view requires for each course
    """
    return {
        'display_name': course.display_name,
        'course_key': unicode(course.location.course_key),
        'url': reverse_course_url('course_handler', course.id),
        'lms_link': get_lms_link_for_item(course.location),
        'rerun_link': _get_rerun_link_for_item(course.id),
        'org': course.display_org_with_default,
        'number': course.display_number_with_default,
        'run': course.location.run
    }


def format_library_for_view(library, user):
    """
    Return a dict of the data which the view requires for each library
    """

    return {
        'display_name': library.display_name,
        'library_key': unicode(library.location.library_key),
        'url': reverse_library_url('library_handler', unicode(library.location.library_key)),
        'org': library.display_org_with_default,
        'number': library.display_number_with_default,
        'can_edit': has_studio_write_access(user, library.location.library_key),
    }


def _get_rerun_link_for_item(course_key):
    """ Returns the rerun link for the given course key. """
    return reverse_course_url('course_rerun_handler', course_key)
