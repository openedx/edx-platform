"""
Utilities to facilitate experimentation
"""

from student.models import CourseEnrollment
from django_comment_common.models import Role
from course_modes.models import get_cosmetic_verified_display_price
from courseware.access import has_staff_access_to_preview_mode
from courseware.date_summary import verified_upgrade_deadline_link, verified_upgrade_link_is_valid
from xmodule.partitions.partitions_service import get_user_partition_groups, get_all_partitions_for_course
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.catalog.utils import get_programs
from openedx.core.djangoapps.waffle_utils import WaffleFlag, WaffleFlagNamespace


# TODO: clean up as part of REVEM-199 (START)
# .. feature_toggle_name: experiments.add_programs
# .. feature_toggle_type: flag
# .. feature_toggle_default: False
# .. feature_toggle_description: Toggle for adding the current course's program information to user metadata
# .. feature_toggle_category: experiments
# .. feature_toggle_use_cases: monitored_rollout
# .. feature_toggle_creation_date: 2019-2-25
# .. feature_toggle_expiration_date: None
# .. feature_toggle_warnings: None
# .. feature_toggle_tickets: REVEM-63, REVEM-198
# .. feature_toggle_status: supported
PROGRAM_INFO_FLAG = WaffleFlag(
    waffle_namespace=WaffleFlagNamespace(name=u'experiments'),
    flag_name=u'add_programs',
    flag_undefined_default=False
)
# TODO: clean up as part of REVEM-199 (END)


def check_and_get_upgrade_link_and_date(user, enrollment=None, course=None):
    """
    For an authenticated user, return a link to allow them to upgrade
    in the specified course.

    Returns the upgrade link and upgrade deadline for a user in a given course given
    that the user is within the window to upgrade defined by our dynamic pacing feature;
    otherwise, returns None for both the link and date.
    """
    if enrollment is None and course is None:
        raise ValueError("Must specify either an enrollment or a course")

    if enrollment:
        if course is None:
            course = enrollment.course
        elif enrollment.course_id != course.id:
            raise ValueError(u"{} refers to a different course than {} which was supplied".format(
                enrollment, course
            ))

        if enrollment.user_id != user.id:
            raise ValueError(u"{} refers to a different user than {} which was supplied".format(
                enrollment, user
            ))

    if enrollment is None:
        enrollment = CourseEnrollment.get_enrollment(user, course.id)

    if user.is_authenticated and verified_upgrade_link_is_valid(enrollment):
        return (
            verified_upgrade_deadline_link(user, course),
            enrollment.upgrade_deadline
        )

    return (None, None)


# TODO: clean up as part of REVEM-199 (START)
def is_enrolled_in_all_courses_in_program(courses_in_program, user_enrollments):
    """
    Determine if the user is enrolled in all courses in this program
    """
    # Get the enrollment course ids here, so we don't need to loop through them for every course run
    enrollment_course_ids = {enrollment.course_id for enrollment in user_enrollments}

    for course in courses_in_program:
        if not is_enrolled_in_course(course, enrollment_course_ids):
            # User is not enrolled in this course, meaning they are not enrolled in all courses in the program
            return False
    # User is enrolled in all courses in the program
    return True


def is_enrolled_in_course(course, enrollment_course_ids):
    """
    Determine if the user is enrolled in this course
    """
    course_runs = course.get('course_runs')
    if course_runs:
        for course_run in course_runs:
            if is_enrolled_in_course_run(course_run, enrollment_course_ids):
                return True
    return False


def is_enrolled_in_course_run(course_run, enrollment_course_ids):
    """
    Determine if the user is enrolled in this course run
    """
    course_run_key = CourseKey.from_string(course_run.get('key'))
    return course_run_key in enrollment_course_ids
# TODO: clean up as part of REVEM-199 (END)


def get_experiment_user_metadata_context(course, user):
    """
    Return a context dictionary with the keys used by the user_metadata.html.
    """
    enrollment_mode = None
    enrollment_time = None
    enrollment = None
    # TODO: clean up as part of REVO-28 (START)
    has_non_audit_enrollments = None
    # TODO: clean up as part of REVO-28 (END)
    # TODO: clean up as part of REVEM-199 (START)
    program_key = None
    # TODO: clean up as part of REVEM-199 (END)
    try:
        # TODO: clean up as part of REVO-28 (START)
        user_enrollments = CourseEnrollment.objects.select_related('course').filter(user_id=user.id)
        audit_enrollments = user_enrollments.filter(mode='audit')
        has_non_audit_enrollments = (len(audit_enrollments) != len(user_enrollments))
        # TODO: clean up as part of REVO-28 (END)
        enrollment = CourseEnrollment.objects.select_related(
            'course'
        ).get(user_id=user.id, course_id=course.id)
        if enrollment.is_active:
            enrollment_mode = enrollment.mode
            enrollment_time = enrollment.created

            # TODO: clean up as part of REVEM-199 (START)
            if PROGRAM_INFO_FLAG.is_enabled():
                programs = get_programs(course=course.id)
                if programs:
                    # A course can be in multiple programs, but we're just grabbing the first one
                    program = programs[0]
                    complete_enrollment = False
                    total_courses = None
                    courses = program.get('courses')
                    if courses is not None:
                        total_courses = len(courses)
                        complete_enrollment = is_enrolled_in_all_courses_in_program(courses, user_enrollments)

                    program_key = {
                        'uuid': program.get('uuid'),
                        'title': program.get('title'),
                        'marketing_url': program.get('marketing_url'),
                        'total_courses': total_courses,
                        'complete_enrollment': complete_enrollment,
                    }
            # TODO: clean up as part of REVEM-199 (END)
    except CourseEnrollment.DoesNotExist:
        pass  # Not enrolled, used the default None values

    # upgrade_link and upgrade_date should be None if user has passed their dynamic pacing deadline.
    upgrade_link, upgrade_date = check_and_get_upgrade_link_and_date(user, enrollment, course)
    has_staff_access = has_staff_access_to_preview_mode(user, course.id)
    forum_roles = []
    if user.is_authenticated:
        forum_roles = list(Role.objects.filter(users=user, course_id=course.id).values_list('name').distinct())

    # get user partition data
    if user.is_authenticated():
        partition_groups = get_all_partitions_for_course(course)
        user_partitions = get_user_partition_groups(course.id, partition_groups, user, 'name')
    else:
        user_partitions = {}

    return {
        'upgrade_link': upgrade_link,
        'upgrade_price': unicode(get_cosmetic_verified_display_price(course)),
        'enrollment_mode': enrollment_mode,
        'enrollment_time': enrollment_time,
        'pacing_type': 'self_paced' if course.self_paced else 'instructor_paced',
        'upgrade_deadline': upgrade_date,
        'course_key': course.id,
        'course_start': course.start,
        'course_end': course.end,
        'has_staff_access': has_staff_access,
        'forum_roles': forum_roles,
        'partition_groups': user_partitions,
        # TODO: clean up as part of REVO-28 (START)
        'has_non_audit_enrollments': has_non_audit_enrollments,
        # TODO: clean up as part of REVO-28 (END)
        # TODO: clean up as part of REVEM-199 (START)
        'program_key_fields': program_key,
        # TODO: clean up as part of REVEM-199 (END)
    }


#TODO START: Clean up REVEM-205
def get_experiment_dashboard_metadata_context(enrollments):
    """
    Given a list of enrollments return a dict of course ids with their prices.
    Utility function for experimental metadata. See experiments/dashboard_metadata.html.
    :param enrollments:
    :return: dict of courses: course price for dashboard metadata
    """
    return {str(enrollment.course): enrollment.course_price for enrollment in enrollments}
#TODO END: Clean up REVEM-205
