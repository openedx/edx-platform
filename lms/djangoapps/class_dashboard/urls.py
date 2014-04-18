"""
Class Dashboard API endpoint urls.
"""

from django.conf.urls import patterns, url

urlpatterns = patterns('',  # nopep8
    # Json request data for metrics for entire course
    url(r'^(?P<course_id>[^/]+/[^/]+/[^/]+)/all_sequential_open_distrib$',
        'class_dashboard.views.all_sequential_open_distrib', name="all_sequential_open_distrib"),

    url(r'^(?P<course_id>[^/]+/[^/]+/[^/]+)/all_problem_grade_distribution$',
        'class_dashboard.views.all_problem_grade_distribution', name="all_problem_grade_distribution"),

    # Json request data for metrics for particular section
    url(r'^(?P<course_id>[^/]+/[^/]+/[^/]+)/problem_grade_distribution/(?P<section>\d+)$',
        'class_dashboard.views.section_problem_grade_distrib', name="section_problem_grade_distrib"),

    # For listing students that opened a sub-section
    url(r'^get_students_opened_subsection$',
        'class_dashboard.dashboard_data.get_students_opened_subsection', name="get_students_opened_subsection"),

    # For listing of students' grade per problem
    url(r'^get_students_problem_grades$',
        'class_dashboard.dashboard_data.get_students_problem_grades', name="get_students_problem_grades"),

    # For generating metrics data as a csv
    url(r'^post_metrics_data_csv_url',
        'class_dashboard.dashboard_data.post_metrics_data_csv', name="post_metrics_data_csv"),
)
