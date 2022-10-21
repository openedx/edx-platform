"""
Queries to get data from database.
"""

from datetime import datetime, timedelta

from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.db.models import Count, OuterRef, Q, Subquery

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
        .count()


def currently_learners() -> int:
    """
    Get total number of learners with last login in the last 3 weeks.
    """
    return User.objects.filter(last_login__gte=datetime.now() - timedelta(weeks=3)).count()


def learners_registered() -> int:
    """
    Get count of learners registered.
    """
    return User.objects.filter(is_active=1).count()


def generated_certificates() -> int:
    """
    Get count of generated certificates.
    """
    return PersistentCourseGrade.objects.filter(passed_timestamp__isnull=False).count()
