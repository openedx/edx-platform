"""
Class Dashboard API endpoint urls.
"""

from django.conf import settings
from django.conf.urls import url

from class_dashboard.views import (
    all_problem_grade_distribution,
    all_sequential_open_distrib,
    section_problem_grade_distrib
)
from class_dashboard.dashboard_data import (
    get_students_opened_subsection,
    get_students_problem_grades,
    post_metrics_data_csv
)

COURSE_ID_PATTERN = settings.COURSE_ID_PATTERN

urlpatterns = [
    # Json request data for metrics for entire course
    url(r'^{}/all_sequential_open_distrib$'.format(settings.COURSE_ID_PATTERN),
        all_sequential_open_distrib, name="all_sequential_open_distrib"),

    url(r'^{}/all_problem_grade_distribution$'.format(settings.COURSE_ID_PATTERN),
        all_problem_grade_distribution, name="all_problem_grade_distribution"),

    # Json request data for metrics for particular section
    url(r'^{}/problem_grade_distribution/(?P<section>\d+)$'.format(settings.COURSE_ID_PATTERN),
        section_problem_grade_distrib, name="section_problem_grade_distrib"),

    # For listing students that opened a sub-section
    url(r'^get_students_opened_subsection$',
        get_students_opened_subsection, name="get_students_opened_subsection"),

    # For listing of students' grade per problem
    url(r'^get_students_problem_grades$',
        get_students_problem_grades, name="get_students_problem_grades"),

    # For generating metrics data as a csv
    url(r'^post_metrics_data_csv_url',
        post_metrics_data_csv, name="post_metrics_data_csv"),
]
