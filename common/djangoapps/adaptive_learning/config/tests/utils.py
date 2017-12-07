"""
Provides helper functions for tests which need
to configure flags related to Adaptive Learning.
"""
from contextlib import contextmanager

from adaptive_learning.config.models import (
    AdaptiveLearningEnabledFlag,
    CourseAdaptiveLearningFlag
)
from request_cache.middleware import RequestCache


@contextmanager
def adaptive_learning_enabled_feature_flags(
    global_flag,
    course_id=None,
    enabled_for_course=False
):
    """
    Sets the global setting and the course-specific
    setting (if the course_id is given) for Adaptive Learning.
    """
    RequestCache.clear_request_cache()
    AdaptiveLearningEnabledFlag.objects.create(enabled=global_flag)
    if course_id:
        CourseAdaptiveLearningFlag.objects.create(
            course_id=course_id, enabled=enabled_for_course
        )
    yield
