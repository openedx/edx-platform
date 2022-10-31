"""
Queries to get data from database.
"""

from datetime import datetime, timedelta

from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.db.models import Count, OuterRef, Q, Subquery

from common.djangoapps.util.query import read_replica_or_default
from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.grades.models import PersistentCourseGrade
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


def get_unique_courses_offered() -> int:
    """
    Get total number of unique courses offered.
    """
    return CourseOverview.objects.annotate(
        count=Subquery(
            CourseEnrollment.objects
                            .filter(course_id=OuterRef('id'))
                            .values('course_id')
                            .annotate(count=Count('course_id'))
                            .values('count')
        ))\
        .filter(count__gt=5)\
        .filter(start__lt=datetime.now())\
        .filter(Q(end__isnull=True) | Q(end__gt=datetime.now()))\
        .using(read_replica_or_default())\
        .count()


def get_active_learners_in_the_last_weeks(weeks: int) -> int:
    """
    Get total number of users with last login in the last weeks.

    Args:
        weeks (int): number of weeks since the last login to considerate as an active learner.
    """
    return User.objects.filter(last_login__gte=datetime.now() - timedelta(weeks=weeks))\
        .using(read_replica_or_default())\
        .count()


def get_registered_learners() -> int:
    """
    Get total number of active learners registered.
    """
    return User.objects.filter(is_active=True)\
        .using(read_replica_or_default())\
        .count()


def get_generated_certificates() -> int:
    """
    Get total number of generated certificates.
    """
    return PersistentCourseGrade.objects.filter(passed_timestamp__isnull=False)\
        .using(read_replica_or_default())\
        .count()


def get_course_enrollments() -> int:
    """
    Get total number of enrollments from users that aren't staff. Course staff members will be included.
    """
    return CourseEnrollment.objects.filter(is_active=True, user__is_superuser=False, user__is_staff=False)\
        .using(read_replica_or_default())\
        .count()
