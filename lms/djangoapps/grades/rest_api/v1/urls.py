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
        fr'^courses/{settings.COURSE_ID_PATTERN}/$',
        views.CourseGradesView.as_view(),
        name='course_grades'
    ),
    url(
        fr'^policy/courses/{settings.COURSE_ID_PATTERN}/$',
        views.CourseGradingPolicy.as_view(),
        name='course_grading_policy'
    ),
    url(
        fr'^gradebook/{settings.COURSE_ID_PATTERN}/$',
        gradebook_views.GradebookView.as_view(),
        name='course_gradebook'
    ),
    url(
        fr'^gradebook/{settings.COURSE_ID_PATTERN}/bulk-update$',
        gradebook_views.GradebookBulkUpdateView.as_view(),
        name='course_gradebook_bulk_update'
    ),
    url(
        fr'^gradebook/{settings.COURSE_ID_PATTERN}/grading-info$',
        gradebook_views.CourseGradingView.as_view(),
        name='course_gradebook_grading_info'
    ),
    url(
        r'^subsection/(?P<subsection_id>.*)/$',
        gradebook_views.SubsectionGradeView.as_view(),
        name='course_grade_overrides'
    ),
]
