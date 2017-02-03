"""
Provides helper functions for tests that want
to configure flags related to persistent grading.
"""
from lms.djangoapps.grades.config.models import PersistentGradesEnabledFlag, CoursePersistentGradesFlag
from contextlib import contextmanager


@contextmanager
def persistent_grades_feature_flags(
        global_flag,
        enabled_for_all_courses=False,
        course_id=None,
        enabled_for_course=False
):
    """
    Most test cases will use a single call to this manager,
    as they need to set the global setting and the course-specific
    setting for a single course.
    """
    PersistentGradesEnabledFlag.objects.create(enabled=global_flag, enabled_for_all_courses=enabled_for_all_courses)
    if course_id:
        CoursePersistentGradesFlag.objects.create(course_id=course_id, enabled=enabled_for_course)
    yield
