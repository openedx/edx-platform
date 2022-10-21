"""
Queries to get data from database.
"""

from datetime import datetime, timedelta
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from common.djangoapps.student.models import CourseEnrollment
from django.contrib.auth.models import User

from django.db.models import Q, Subquery, OuterRef, Count

def get_unique_courses_offered() -> int:
    """
    Get total number of unique courses offered.
    """
    return CourseOverview.objects.annotate(
        count = Subquery(
            CourseEnrollment.objects
                .filter(course_id=OuterRef('id'))
                .values('course_id')
                .annotate(count=Count('course_id'))
                .values('count')
                ))\
        .filter(count__gt=5)\
        .filter(start__lt=datetime.now())\
        .filter(Q(end__isnull=True)|Q(end__gt=datetime.now()))\
        .count()

def currently_learners() -> int:
    """
    Get total number of learners with last login in the last 3 weeks.
    """
    return User.objects.filter(last_login__gte=datetime.now() - timedelta(weeks=3)).count()
