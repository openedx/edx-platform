""" Grades API v1 URLs. """


from django.conf import settings
from django.conf.urls import url

from lms.djangoapps.grades.rest_api.v1 import gradebook_views, views

app_name = 'lms.djangoapps.grades'

urlpatterns = [
    url(
        r'^courses/$',
        views.CourseGradesView.as_view(),
        name='course_grades'
    ),
    url(
        r'^courses/{course_id}/$'.format(course_id=settings.COURSE_ID_PATTERN),
        views.CourseGradesView.as_view(),
        name='course_grades'
    ),
    url(
        r'^policy/courses/{course_id}/$'.format(course_id=settings.COURSE_ID_PATTERN),
        views.CourseGradingPolicy.as_view(),
        name='course_grading_policy'
    ),
    url(
        r'^gradebook/{course_id}/$'.format(course_id=settings.COURSE_ID_PATTERN),
        gradebook_views.GradebookView.as_view(),
        name='course_gradebook'
    ),
    url(
        r'^gradebook/{course_id}/bulk-update$'.format(course_id=settings.COURSE_ID_PATTERN),
        gradebook_views.GradebookBulkUpdateView.as_view(),
        name='course_gradebook_bulk_update'
    ),
    url(
        r'^gradebook/{course_id}/grading-info$'.format(course_id=settings.COURSE_ID_PATTERN),
        gradebook_views.CourseGradingView.as_view(),
        name='course_gradebook_grading_info'
    ),
    url(
        r'^subsection/(?P<subsection_id>.*)/$',
        gradebook_views.SubsectionGradeView.as_view(),
        name='course_grade_overrides'
    ),
]
