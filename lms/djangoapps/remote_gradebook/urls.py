"""
Remote Gradebook API endpoint urls.
"""

from django.conf.urls import url

from remote_gradebook import views

urlpatterns = [
    url(r'^get_remote_gradebook_sections$', views.get_remote_gradebook_sections, name="get_remote_gradebook_sections"),
    url(r'^get_assignment_names$', views.get_assignment_names, name="get_assignment_names"),
    url(r'^get_non_staff_enrollments$', views.get_non_staff_enrollments, name="get_non_staff_enrollments"),
    url(r'^list_remote_enrolled_students$',
        views.list_matching_remote_enrolled_students, name="list_remote_enrolled_students"),
    url(r'^list_remote_students_in_section$',
        views.list_remote_students_in_section, name="list_remote_students_in_section"),
    url(r'^add_enrollments_using_remote_gradebook$',
        views.add_enrollments_using_remote_gradebook, name="add_enrollments_using_remote_gradebook"),
    url(r'^list_remote_assignments$', views.list_remote_assignments, name="list_remote_assignments"),
    url(r'^display_assignment_grades$', views.display_assignment_grades, name="display_assignment_grades"),
    url(r'^export_assignment_grades_to_rg$',
        views.export_assignment_grades_to_rg, name="export_assignment_grades_to_rg"),
    url(r'^export_assignment_grades_csv$',
        views.export_assignment_grades_csv, name="export_assignment_grades_csv"),
]
