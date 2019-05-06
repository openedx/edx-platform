"""
Provides Python APIs exposed from Grades models.
"""
from lms.djangoapps.grades.models import (
    PersistentCourseGrade as _PersistentCourseGrade,
    PersistentSubsectionGrade as _PersistentSubsectionGrade,
    PersistentSubsectionGradeOverride as _PersistentSubsectionGradeOverride,
    VisibleBlocks as _VisibleBlocks,
)


def prefetch_grade_overrides_and_visible_blocks(user, course_key):
    _PersistentSubsectionGradeOverride.prefetch(user.id, course_key)
    _VisibleBlocks.bulk_read(user.id, course_key)


def prefetch_course_grades(course_key, users):
    _PersistentCourseGrade.prefetch(course_key, users)


def prefetch_course_and_subsection_grades(course_key, users):
    _PersistentCourseGrade.prefetch(course_key, users)
    _PersistentSubsectionGrade.prefetch(course_key, users)


def clear_prefetched_course_grades(course_key):
    _PersistentCourseGrade.clear_prefetched_data(course_key)
    _PersistentSubsectionGrade.clear_prefetched_data(course_key)


def clear_prefetched_course_and_subsection_grades(course_key):
    _PersistentCourseGrade.clear_prefetched_data(course_key)


def get_recently_modified_grades(course_keys, start_date, end_date):
    """
    Returns a QuerySet of PersistentCourseGrade objects filtered by the input
    parameters and ordered by modified date.
    """
    grade_filter_args = {}
    if course_keys:
        grade_filter_args['course_id__in'] = course_keys
    if start_date:
        grade_filter_args['modified__gte'] = start_date
    if end_date:
        grade_filter_args['modified__lte'] = end_date

    return _PersistentCourseGrade.objects.filter(**grade_filter_args).order_by('modified')
