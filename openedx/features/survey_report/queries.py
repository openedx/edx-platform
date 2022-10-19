"""
Queries to get data from database.
"""

from datetime import datetime
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from common.djangoapps.student.models import CourseEnrollment


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
