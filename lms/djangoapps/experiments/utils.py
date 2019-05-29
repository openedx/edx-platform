"""
Utilities to facilitate experimentation
"""

from __future__ import absolute_import

import hashlib
import logging
import re
from decimal import Decimal

import six
from django.utils.timezone import now
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.course_modes.models import format_course_price, get_cosmetic_verified_display_price
from courseware.access import has_staff_access_to_preview_mode
from courseware.date_summary import verified_upgrade_deadline_link, verified_upgrade_link_is_valid
from lms.djangoapps.commerce.utils import EcommerceService
from openedx.core.djangoapps.catalog.utils import get_programs
from openedx.core.djangoapps.django_comment_common.models import Role
from openedx.core.djangoapps.waffle_utils import WaffleFlag, WaffleFlagNamespace
from openedx.features.course_duration_limits.access import get_user_course_expiration_date
from openedx.features.course_duration_limits.models import CourseDurationLimitConfig
from student.models import CourseEnrollment
from xmodule.partitions.partitions_service import get_all_partitions_for_course, get_user_partition_groups

logger = logging.getLogger(__name__)


# TODO: clean up as part of REVEM-199 (START)
experiments_namespace = WaffleFlagNamespace(name=u'experiments')

# .. toggle_name: experiments.add_programs
# .. toggle_type: feature_flag
# .. toggle_default: True
# .. toggle_description: Toggle for adding the current course's program information to user metadata
# .. toggle_category: experiments
# .. toggle_use_cases: monitored_rollout
# .. toggle_creation_date: 2019-2-25
# .. toggle_expiration_date: None
# .. toggle_warnings: None
# .. toggle_tickets: REVEM-63, REVEM-198
# .. toggle_status: supported
PROGRAM_INFO_FLAG = WaffleFlag(
    waffle_namespace=experiments_namespace,
    flag_name=u'add_programs',
    flag_undefined_default=True
)

# .. toggle_name: experiments.add_dashboard_info
# .. toggle_type: feature_flag
# .. toggle_default: True
# .. toggle_description: Toggle for adding info about each course to the dashboard metadata
# .. toggle_category: experiments
# .. toggle_use_cases: monitored_rollout
# .. toggle_creation_date: 2019-3-28
# .. toggle_expiration_date: None
# .. toggle_warnings: None
# .. toggle_tickets: REVEM-118
# .. toggle_status: supported
DASHBOARD_INFO_FLAG = WaffleFlag(experiments_namespace,
                                 u'add_dashboard_info',
                                 flag_undefined_default=True)
# TODO END: clean up as part of REVEM-199 (End)

# .. toggle_name: experiments.add_audit_deadline
# .. toggle_type: feature_flag
# .. toggle_default: True
# .. toggle_description: Toggle for adding the current course's audit deadline
# .. toggle_category: experiments
# .. toggle_use_cases: monitored_rollout
# .. toggle_creation_date: 2019-5-7
# .. toggle_expiration_date: None
# .. toggle_warnings: None
# .. toggle_tickets: REVEM-329
# .. toggle_status: supported
AUDIT_DEADLINE_FLAG = WaffleFlag(
    waffle_namespace=experiments_namespace,
    flag_name=u'add_audit_deadline',
    flag_undefined_default=True
)

# .. toggle_name: experiments.deprecated_metadata
# .. toggle_type: feature_flag
# .. toggle_default: True
# .. toggle_description: Toggle for using the deprecated method for calculating user metadata
# .. toggle_category: experiments
# .. toggle_use_cases: monitored_rollout
# .. toggle_creation_date: 2019-5-8
# .. toggle_expiration_date: None
# .. toggle_warnings: None
# .. toggle_tickets: REVEM-350
# .. toggle_status: supported
DEPRECATED_METADATA = WaffleFlag(
    waffle_namespace=experiments_namespace,
    flag_name=u'deprecated_metadata',
    flag_undefined_default=False
)


def check_and_get_upgrade_link_and_date(user, enrollment=None, course=None):
    """
    For an authenticated user, return a link to allow them to upgrade
    in the specified course.

    Returns the upgrade link and upgrade deadline for a user in a given course given
    that the user is within the window to upgrade defined by our dynamic pacing feature;
    otherwise, returns None for both the link and date.
    """
    if enrollment is None and course is None:
        logger.warn(u'Must specify either an enrollment or a course')
        return (None, None)

    if enrollment:
        if course is None:
            course = enrollment.course
        elif enrollment.course_id != course.id:
            logger.warn(u'{} refers to a different course than {} which was supplied. Enrollment course id={}, '
                        u'repr={!r}, deprecated={}. Course id={}, repr={!r}, deprecated={}.'
                        .format(enrollment,
                                course,
                                enrollment.course_id,
                                enrollment.course_id,
                                enrollment.course_id.deprecated,
                                course.id,
                                course.id,
                                course.id.deprecated
                                )
                        )
            return (None, None)

        if enrollment.user_id != user.id:
            logger.warn(u'{} refers to a different user than {} which was supplied. Enrollment user id={}, repr={!r}. '
                        u'User id={}, repr={!r}.'.format(enrollment,
                                                         user,
                                                         enrollment.user_id,
                                                         enrollment.user_id,
                                                         user.id,
                                                         user.id,
                                                         )
                        )
            return (None, None)

    if enrollment is None:
        enrollment = CourseEnrollment.get_enrollment(user, course.id)

    if user.is_authenticated and verified_upgrade_link_is_valid(enrollment):
        return (
            verified_upgrade_deadline_link(user, course),
            enrollment.upgrade_deadline
        )

    return (None, None)


# TODO: clean up as part of REVEM-199 (START)
def get_program_price_and_skus(courses):
    """
    Get the total program price and purchase skus from these courses in the program
    """
    program_price = 0
    skus = []

    for course in courses:
        course_price, course_sku = get_course_entitlement_price_and_sku(course)
        if course_price is not None and course_sku is not None:
            program_price = Decimal(program_price) + Decimal(course_price)
            skus.append(course_sku)

    if program_price <= 0:
        program_price = None
        skus = None
    else:
        program_price = format_course_price(program_price)
        program_price = six.text_type(program_price)

    return program_price, skus


def get_course_entitlement_price_and_sku(course):
    """
    Get the entitlement price and sku from this course.
    Try to get them from the first non-expired, verified entitlement that has a price and a sku. If that doesn't work,
    fall back to the first non-expired, verified course run that has a price and a sku.
    """
    for entitlement in course.get('entitlements', []):
        if entitlement.get('mode') == 'verified' and entitlement['price'] and entitlement['sku']:
            expires = entitlement.get('expires')
            if not expires or expires > now():
                return entitlement['price'], entitlement['sku']

    course_runs = course.get('course_runs', [])
    published_course_runs = [run for run in course_runs if run['status'] == 'published']
    for published_course_run in published_course_runs:
        for seat in published_course_run['seats']:
            if seat.get('type') == 'verified' and seat['price'] and seat['sku']:
                price = Decimal(seat.get('price'))
                return price, seat.get('sku')

    return None, None


def get_unenrolled_courses(courses, user_enrollments):
    """
    Given a list of courses and a list of user enrollments, return the courses in which the user is not enrolled.
    Depending on the enrollments that are passed in, this method can be used to determine the courses in a program in
    which the user has not yet enrolled or the courses in a program for which the user has not yet purchased a
    certificate.
    """
    # Get the enrollment course ids here, so we don't need to loop through them for every course run
    enrollment_course_ids = {enrollment.course_id for enrollment in user_enrollments}
    unenrolled_courses = []

    for course in courses:
        if not is_enrolled_in_course(course, enrollment_course_ids):
            unenrolled_courses.append(course)
    return unenrolled_courses


def is_enrolled_in_all_courses(courses, user_enrollments):
    """
    Determine if the user is enrolled in all of the courses
    """
    # Get the enrollment course ids here, so we don't need to loop through them for every course run
    enrollment_course_ids = {enrollment.course_id for enrollment in user_enrollments}

    for course in courses:
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
    key = None
    try:
        key = course_run.get('key')
        course_run_key = CourseKey.from_string(key)
        return course_run_key in enrollment_course_ids
    except InvalidKeyError:
        logger.warn(
            u'Unable to determine if user was enrolled since the course key {} is invalid'.format(key)
        )
        return False  # Invalid course run key. Assume user is not enrolled.


def get_dashboard_course_info(user, dashboard_enrollments):
    """
    Given a list of enrollments shown on the dashboard, return a dict of course ids and experiment info for that course
    """
    course_info = None
    if DASHBOARD_INFO_FLAG.is_enabled():
        # Get the enrollments here since the dashboard filters out those with completed entitlements
        user_enrollments = CourseEnrollment.objects.select_related('course').filter(user_id=user.id)
        audit_enrollments = user_enrollments.filter(mode='audit')

        course_info = {
            str(dashboard_enrollment.course): get_base_experiment_metadata_context(dashboard_enrollment.course,
                                                                                   user,
                                                                                   dashboard_enrollment,
                                                                                   user_enrollments,
                                                                                   audit_enrollments)
            for dashboard_enrollment in dashboard_enrollments
        }
    return course_info
# TODO: clean up as part of REVEM-199 (END)


def get_experiment_user_metadata_context(course, user):
    """
    Return a context dictionary with the keys used by the user_metadata.html.
    """
    if DEPRECATED_METADATA.is_enabled():
        return get_deprecated_experiment_user_metadata_context(course, user)

    enrollment = None
    # TODO: clean up as part of REVO-28 (START)
    user_enrollments = None
    audit_enrollments = None
    has_non_audit_enrollments = False
    try:
        user_enrollments = CourseEnrollment.objects.select_related('course').filter(user_id=user.id)
        audit_enrollments = user_enrollments.filter(mode='audit')
        has_non_audit_enrollments = (len(audit_enrollments) != len(user_enrollments))
        # TODO: clean up as part of REVO-28 (END)
        enrollment = CourseEnrollment.objects.select_related(
            'course'
        ).get(user_id=user.id, course_id=course.id)
    except CourseEnrollment.DoesNotExist:
        pass  # Not enrolled, use the default values

    context = get_base_experiment_metadata_context(course, user, enrollment, user_enrollments, audit_enrollments)
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

    # TODO: clean up as part of REVO-28 (START)
    context['has_non_audit_enrollments'] = has_non_audit_enrollments
    # TODO: clean up as part of REVO-28 (END)
    context['has_staff_access'] = has_staff_access
    context['forum_roles'] = forum_roles
    context['partition_groups'] = user_partitions
    return context


# pylint: disable=too-many-statements
def get_deprecated_experiment_user_metadata_context(course, user):
    """
    Return a context dictionary with the keys used by the user_metadata.html. This is deprecated and will be removed
    once we have confirmed that its replacement functions as intended.
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
        # TODO: clean up as part of REVEM-199 (START)
        if PROGRAM_INFO_FLAG.is_enabled():
            programs = get_programs(course=course.id)
            if programs:
                # A course can be in multiple programs, but we're just grabbing the first one
                program = programs[0]
                complete_enrollment = False
                has_courses_left_to_purchase = False
                total_courses = None
                courses = program.get('courses')
                courses_left_to_purchase_price = None
                courses_left_to_purchase_url = None
                program_uuid = program.get('uuid')
                status = None
                is_eligible_for_one_click_purchase = None
                if courses is not None:
                    total_courses = len(courses)
                    complete_enrollment = is_enrolled_in_all_courses(courses, user_enrollments)
                    status = program.get('status')
                    is_eligible_for_one_click_purchase = program.get('is_program_eligible_for_one_click_purchase')
                    # Get the price and purchase URL of the program courses the user has yet to purchase. Say a
                    # program has 3 courses (A, B and C), and the user previously purchased a certificate for A.
                    # The user is enrolled in audit mode for B. The "left to purchase price" should be the price of
                    # B+C.
                    non_audit_enrollments = [en for en in user_enrollments if en not in
                                             audit_enrollments]
                    courses_left_to_purchase = get_unenrolled_courses(courses, non_audit_enrollments)
                    if courses_left_to_purchase:
                        has_courses_left_to_purchase = True
                        if is_eligible_for_one_click_purchase:
                            courses_left_to_purchase_price, courses_left_to_purchase_skus = \
                                get_program_price_and_skus(courses_left_to_purchase)
                            if courses_left_to_purchase_skus:
                                courses_left_to_purchase_url = EcommerceService().get_checkout_page_url(
                                    *courses_left_to_purchase_skus, program_uuid=program_uuid)

                program_key = {
                    'uuid': program_uuid,
                    'title': program.get('title'),
                    'marketing_url': program.get('marketing_url'),
                    'status': status,
                    'is_eligible_for_one_click_purchase': is_eligible_for_one_click_purchase,
                    'total_courses': total_courses,
                    'complete_enrollment': complete_enrollment,
                    'has_courses_left_to_purchase': has_courses_left_to_purchase,
                    'courses_left_to_purchase_price': courses_left_to_purchase_price,
                    'courses_left_to_purchase_url': courses_left_to_purchase_url,
                }
        # TODO: clean up as part of REVEM-199 (END)
        enrollment = CourseEnrollment.objects.select_related(
            'course'
        ).get(user_id=user.id, course_id=course.id)
        if enrollment.is_active:
            enrollment_mode = enrollment.mode
            enrollment_time = enrollment.created
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
        'upgrade_price': six.text_type(get_cosmetic_verified_display_price(course)),
        'enrollment_mode': enrollment_mode,
        'enrollment_time': enrollment_time,
        'pacing_type': 'self_paced' if course.self_paced else 'instructor_paced',
        'upgrade_deadline': upgrade_date,
        'audit_access_deadline': get_audit_access_expiration(user, course),
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


def get_base_experiment_metadata_context(course, user, enrollment, user_enrollments, audit_enrollments):
    """
    Return a context dictionary with the keys used by dashboard_metadata.html and user_metadata.html
    """
    enrollment_mode = None
    enrollment_time = None
    # TODO: clean up as part of REVEM-199 (START)
    program_key = get_program_context(course, user_enrollments, audit_enrollments)
    # TODO: clean up as part of REVEM-199 (END)
    if enrollment and enrollment.is_active:
        enrollment_mode = enrollment.mode
        enrollment_time = enrollment.created

    # upgrade_link and upgrade_date should be None if user has passed their dynamic pacing deadline.
    upgrade_link, upgrade_date = check_and_get_upgrade_link_and_date(user, enrollment, course)

    return {
        'upgrade_link': upgrade_link,
        'upgrade_price': six.text_type(get_cosmetic_verified_display_price(course)),
        'enrollment_mode': enrollment_mode,
        'enrollment_time': enrollment_time,
        'pacing_type': 'self_paced' if course.self_paced else 'instructor_paced',
        'upgrade_deadline': upgrade_date,
        'audit_access_deadline': get_audit_access_expiration(user, course),
        'course_key': course.id,
        'course_start': course.start,
        'course_end': course.end,
        # TODO: clean up as part of REVEM-199 (START)
        'program_key_fields': program_key,
        # TODO: clean up as part of REVEM-199 (END)
    }


def get_audit_access_expiration(user, course):
    """
    Return the expiration date for the user's audit access to this course.
    """
    if AUDIT_DEADLINE_FLAG.is_enabled():
        if not CourseDurationLimitConfig.enabled_for_enrollment(user=user, course_key=course.id):
            return None

        return get_user_course_expiration_date(user, course)
    return None


# TODO: clean up as part of REVEM-199 (START)
def get_program_context(course, user_enrollments, audit_enrollments):
    """
    Return a context dictionary with program information.
    """
    program_key = None
    if PROGRAM_INFO_FLAG.is_enabled():
        programs = get_programs(course=course.id)
        if programs:
            # A course can be in multiple programs, but we're just grabbing the first one
            program = programs[0]
            complete_enrollment = False
            has_courses_left_to_purchase = False
            total_courses = None
            courses = program.get('courses')
            courses_left_to_purchase_price = None
            courses_left_to_purchase_url = None
            program_uuid = program.get('uuid')
            is_eligible_for_one_click_purchase = program.get('is_program_eligible_for_one_click_purchase')
            if courses is not None:
                total_courses = len(courses)
                complete_enrollment = is_enrolled_in_all_courses(courses, user_enrollments)

                # Get the price and purchase URL of the program courses the user has yet to purchase. Say a
                # program has 3 courses (A, B and C), and the user previously purchased a certificate for A.
                # The user is enrolled in audit mode for B. The "left to purchase price" should be the price of
                # B+C.
                non_audit_enrollments = [en for en in user_enrollments if en not in audit_enrollments]
                courses_left_to_purchase = get_unenrolled_courses(courses, non_audit_enrollments)
                if courses_left_to_purchase:
                    has_courses_left_to_purchase = True
                if courses_left_to_purchase and is_eligible_for_one_click_purchase:
                    courses_left_to_purchase_price, courses_left_to_purchase_skus = \
                        get_program_price_and_skus(courses_left_to_purchase)
                    if courses_left_to_purchase_skus:
                        courses_left_to_purchase_url = EcommerceService().get_checkout_page_url(
                            *courses_left_to_purchase_skus, program_uuid=program_uuid)

            program_key = {
                'uuid': program_uuid,
                'title': program.get('title'),
                'marketing_url': program.get('marketing_url'),
                'status': program.get('status'),
                'is_eligible_for_one_click_purchase': is_eligible_for_one_click_purchase,
                'total_courses': total_courses,
                'complete_enrollment': complete_enrollment,
                'has_courses_left_to_purchase': has_courses_left_to_purchase,
                'courses_left_to_purchase_price': courses_left_to_purchase_price,
                'courses_left_to_purchase_url': courses_left_to_purchase_url,
            }
    return program_key
# TODO: clean up as part of REVEM-199 (START)


# TODO START: Clean up REVEM-205
def get_experiment_dashboard_metadata_context(enrollments):
    """
    Given a list of enrollments return a dict of course ids with their prices.
    Utility function for experimental metadata. See experiments/dashboard_metadata.html.
    :param enrollments:
    :return: dict of courses: course price for dashboard metadata
    """
    return {str(enrollment.course): enrollment.course_price for enrollment in enrollments}
# TODO END: Clean up REVEM-205


def stable_bucketing_hash_group(group_name, group_count, username):
    """
    Return the bucket that a user should be in for a given stable bucketing assignment.

    This function has been verified to return the same values as the stable bucketing
    functions in javascript and the master experiments table.

    Arguments:
        group_name: The name of the grouping/experiment.
        group_count: How many groups to bucket users into.
        username: The username of the user being bucketed.
    """
    hasher = hashlib.md5()
    hasher.update(group_name.encode('utf-8'))
    hasher.update(username.encode('utf-8'))
    hash_str = hasher.hexdigest()

    return int(re.sub('[8-9a-f]', '1', re.sub('[0-7]', '0', hash_str)), 2) % group_count
