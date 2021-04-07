"""
This module contains utility functions for grading.
"""


import logging
from contextlib import contextmanager
from datetime import timedelta

from django.utils import timezone

from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.roles import BulkRoleCache
from lms.djangoapps.grades.api import (
    CourseGradeFactory,
    clear_prefetched_course_and_subsection_grades,
    is_writable_gradebook_enabled,
    prefetch_course_and_subsection_grades
)
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.course_groups import cohorts

from .config.waffle import ENFORCE_FREEZE_GRADE_AFTER_COURSE_END, waffle_flags

log = logging.getLogger(__name__)


def are_grades_frozen(course_key):
    """ Returns whether grades are frozen for the given course. """
    if waffle_flags()[ENFORCE_FREEZE_GRADE_AFTER_COURSE_END].is_enabled(course_key):
        course = CourseOverview.get_from_id(course_key)
        if course.end:
            freeze_grade_date = course.end + timedelta(30)
            now = timezone.now()
            return now > freeze_grade_date
    return False


def serialize_user_grade(user, course_key, course_grade):
    """
    Serialize a single grade to dict to use in Responses
    """
    return {
        'username': user.username,
        # per business requirements, email should only be visible for students in masters track only
        'email': user.email if getattr(user, 'enrollment_mode', '') == 'masters' else '',
        'course_id': str(course_key),
        'passed': course_grade.passed,
        'percent': course_grade.percent,
        'letter_grade': course_grade.letter_grade,
    }


def section_breakdown(course, graded_subsections, course_grade):
    """
    Given a course_grade and a list of graded subsections for a given course,
    returns a list of grade data broken down by subsection.

    Args:
        course: A Course Descriptor object
        graded_subsections: A list of graded subsection objects in the given course.
        course_grade: A CourseGrade object.
    """
    breakdown = []
    default_labeler = get_default_short_labeler(course)

    for subsection in graded_subsections:
        subsection_grade = course_grade.subsection_grade(subsection.location)
        short_label = default_labeler(subsection_grade.format)

        attempted = False
        score_earned = 0
        score_possible = 0

        # For ZeroSubsectionGrades, we don't want to crawl the subsection's
        # subtree to find the problem scores specific to this user
        # (ZeroSubsectionGrade.attempted_graded is always False).
        # We've already fetched the whole course structure in a non-user-specific way
        # when creating `graded_subsections`.  Looking at the problem scores
        # specific to this user (the user in `course_grade.user`) would require
        # us to re-fetch the user-specific course structure from the modulestore,
        # which is a costly operation.  So we only drill into the `graded_total`
        # attribute if the user has attempted this graded subsection, or if there
        # has been a grade override applied.
        if subsection_grade.attempted_graded or subsection_grade.override:
            attempted = True
            score_earned = subsection_grade.graded_total.earned
            score_possible = subsection_grade.graded_total.possible

        # TODO: https://openedx.atlassian.net/browse/EDUCATOR-3559 -- Some fields should be renamed, others removed:
        # 'displayed_value' should maybe be 'description_percent'
        # 'grade_description' should be 'description_ratio'
        breakdown.append({
            'attempted': attempted,
            'category': subsection_grade.format,
            'label': short_label,
            'module_id': str(subsection_grade.location),
            'percent': subsection_grade.percent_graded,
            'score_earned': score_earned,
            'score_possible': score_possible,
            'subsection_name': subsection_grade.display_name,
        })
    return breakdown


@contextmanager
def bulk_gradebook_view_context(course_key, users):
    """
    Prefetches all course and subsection grades in the given course for the given
    list of users, also, fetch all the score relavant data,
    storing the result in a RequestCache and deleting grades on context exit.
    """
    prefetch_course_and_subsection_grades(course_key, users)
    CourseEnrollment.bulk_fetch_enrollment_states(users, course_key)
    cohorts.bulk_cache_cohorts(course_key, users)
    BulkRoleCache.prefetch(users)
    try:
        yield
    finally:
        clear_prefetched_course_and_subsection_grades(course_key)


def paginate_users(course_key, course_enrollment_filter=None, related_models=None, annotations=None):
    """
    Args:
        course_key (CourseLocator): The course to retrieve grades for.
        course_enrollment_filter: Optional list of Q objects to pass
        to `CourseEnrollment.filter()`.
        related_models: Optional list of related models to join to the CourseEnrollment table.
        annotations: Optional dict of fields to add to the queryset via annotation

    Returns:
        A list of users, pulled from a paginated queryset of enrollments, who are enrolled in the given course.
    """
    queryset = CourseEnrollment.objects
    if annotations:
        queryset = queryset.annotate(**annotations)

    filter_args = [
        Q(course_id=course_key) & Q(is_active=True)
    ]
    filter_args.extend(course_enrollment_filter or [])

    enrollments_in_course = use_read_replica_if_available(
        queryset.filter(*filter_args)
    )
    if related_models:
        enrollments_in_course = enrollments_in_course.select_related(*related_models)

    paged_enrollments = self.paginate_queryset(enrollments_in_course)
    retlist = []
    for enrollment in paged_enrollments:
        enrollment.user.enrollment_mode = enrollment.mode
        retlist.append(enrollment.user)
        return retlist


def gradebook_entry(user, course, graded_subsections, course_grade):
    """
    Returns a dictionary of course- and subsection-level grade data for
    a given user in a given course.

    Args:
        user: A User object.
        course: A Course Descriptor object.
        graded_subsections: A list of graded subsections in the given course.
        course_grade: A CourseGrade object.
    """
    user_entry = serialize_user_grade(user, course.id, course_grade)
    breakdown = section_breakdown(course, graded_subsections, course_grade)

    user_entry['section_breakdown'] = breakdown
    user_entry['progress_page_url'] = reverse(
        'student_progress',
        kwargs=dict(course_id=str(course.id), student_id=user.id)
    )
    user_entry['user_id'] = user.id
    user_entry['full_name'] = user.profile.name

    external_user_key = get_external_key_by_user_and_course(user, course.id)
    if external_user_key:
        user_entry['external_user_key'] = external_user_key

    return user_entry


def get_subsection_grades_for_a_learner(course_key, username):

    course = get_course_by_id(course_key, depth=None)

    # We fetch the entire course structure up-front, and use this when iterating
    # over users to determine their subsection grades.  We purposely avoid fetching
    # the user-specific course structure for each user, because that is very expensive.
    course_data = CourseData(user=None, course=course)
    graded_subsections = list(grades_context.graded_subsections_for_course(course_data.collected_structure))

    q_objects = []
    annotations = {}
    search_term = username
    q_objects.append(
        Q(user__username__icontains=search_term) |
        Q(programcourseenrollment__program_enrollment__external_user_key__icontains=search_term) |
        Q(user__email__icontains=search_term)
    )

    entries = []
    related_models = ['user']
    users = paginate_users(course_key, q_objects, related_models, annotations=annotations)

    with bulk_gradebook_view_context(course_key, users):
        for user, course_grade, exc in CourseGradeFactory().iter(
            users, course_key=course_key, collected_block_structure=course_data.collected_structure
        ):
            if not exc:
                entry = gradebook_entry(user, course, graded_subsections, course_grade)
                entries.append(entry)

    return entries
