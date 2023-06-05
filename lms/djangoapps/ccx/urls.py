"""
URLs for the CCX Feature.
"""


from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^ccx_coach$', views.dashboard, name='ccx_coach_dashboard'),
    url(r'^create_ccx$', views.create_ccx, name='create_ccx'),
    url(r'^save_ccx$', views.save_ccx, name='save_ccx'),
    url(r'^ccx_schedule$', views.ccx_schedule, name='ccx_schedule'),
    url(r'^ccx-manage-students$', views.ccx_students_management, name='ccx-manage-students'),

    # Grade book
    url(r'^ccx_gradebook$', views.ccx_gradebook, name='ccx_gradebook'),
    url(r'^ccx_gradebook/(?P<offset>[0-9]+)$', views.ccx_gradebook, name='ccx_gradebook'),

    url(r'^ccx_grades.csv$', views.ccx_grades_csv, name='ccx_grades_csv'),
    url(r'^ccx_set_grading_policy$', views.set_grading_policy, name='ccx_set_grading_policy'),
]
