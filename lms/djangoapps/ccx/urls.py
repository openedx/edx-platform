"""
URLs for the CCX Feature.
"""
from django.conf.urls import url

from ccx.views import (
    dashboard,
    create_ccx,
    save_ccx,
    ccx_invite,
    ccx_schedule,
    ccx_student_management,
    ccx_gradebook,
    ccx_grades_csv,
    set_grading_policy
)

urlpatterns = [
    url(r'^ccx_coach$', dashboard, name='ccx_coach_dashboard'),
    url(r'^create_ccx$', create_ccx, name='create_ccx'),
    url(r'^save_ccx$', save_ccx, name='save_ccx'),
    url(r'^ccx_invite$', ccx_invite, name='ccx_invite'),
    url(r'^ccx_schedule$', ccx_schedule, name='ccx_schedule'),
    url(r'^ccx_manage_student$', ccx_student_management, name='ccx_manage_student'),

    # Grade book
    url(r'^ccx_gradebook$', ccx_gradebook, name='ccx_gradebook'),
    url(r'^ccx_gradebook/(?P<offset>[0-9]+)$', ccx_gradebook, name='ccx_gradebook'),

    url(r'^ccx_grades.csv$', ccx_grades_csv, name='ccx_grades_csv'),
    url(r'^ccx_set_grading_policy$', set_grading_policy, name='ccx_set_grading_policy'),
]
