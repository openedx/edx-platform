"""
URLs for the CCX Feature.
"""
from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(r'^ccx_coach$',
        'ccx.views.dashboard', name='ccx_coach_dashboard'),
    url(r'^create_ccx$',
        'ccx.views.create_ccx', name='create_ccx'),
    url(r'^save_ccx$',
        'ccx.views.save_ccx', name='save_ccx'),
    url(r'^ccx_invite$',
        'ccx.views.ccx_invite', name='ccx_invite'),
    url(r'^ccx_schedule$',
        'ccx.views.ccx_schedule', name='ccx_schedule'),
    url(r'^ccx_manage_student$',
        'ccx.views.ccx_student_management', name='ccx_manage_student'),

    # Grade book
    url(r'^ccx_gradebook$',
        'ccx.views.ccx_gradebook', name='ccx_gradebook'),
    url(r'^ccx_gradebook/(?P<offset>[0-9]+)$',
        'ccx.views.ccx_gradebook', name='ccx_gradebook'),

    url(r'^ccx_grades.csv$',
        'ccx.views.ccx_grades_csv', name='ccx_grades_csv'),
    url(r'^ccx_set_grading_policy$',
        'ccx.views.set_grading_policy', name='ccx_set_grading_policy'),
)
