"""
URLs for student app
"""


from django.conf import settings
from django.urls import path, re_path
from django.views.decorators.csrf import csrf_exempt

from . import views

urlpatterns = [

    re_path(r'^extras/join_zoom_meeting$', views.join_zoom_meeting, name = "join_zoom_meeting"),
    re_path(r'^extras/{}/join_zoom'.format(settings.COURSE_ID_PATTERN), views.extras_join_zoom, name = 'extras_join_zoom'),

    re_path(r'^extras/course_enroll_user/', csrf_exempt(views.extras_course_enroll_user), name = 'extras_course_enroll_user'),

    re_path(r'^extras/gradebook$', views.extras_get_moodle_grades, name = "extras_get_moodle_grades"),
    re_path(r'^attendance_report', views.attendance_report, name = "attendance_report"),
    re_path(r'^extras/user_details$', views.extras_userdetails, name = 'extras_userdetails'),
    re_path(r'^notebook_submissions', views.extras_notebook_submissions, name = 'extras_notebook_submissions'),

    re_path(r'^extras/reset_password_link', views.extras_reset_password_link, name = "extras_reset_password_link"),
    re_path(r'^extras/emiitk_get_grades', views.extras_emiitk_get_grades, name = "extras_emiitk_get_grades"),
    re_path(r'^extras/start_mettl_test', views.extras_start_mettl_test, name = "extras_start_mettl_test"),
    re_path(r'^extras/get_mettl_report', views.extras_get_mettl_report, name = "extras_get_mettl_report"), 
    re_path(r'^extras/update_lti_grades', views.extras_update_lti_grades, name = "extras_update_lti_grades"),
    re_path(r'^extras/get_peer_profiles', views.extras_get_peer_profiles, name = "extras_get_peer_profiles"),
    
    re_path(r'^extras/certificate', views.extras_certificate, name = "extras_certificate"),
    re_path(r'^extras/transcript', views.extras_transcript, name = "extras_transcript"),
    

    re_path(r'^extras/get_user_enrolled_courses', views.extras_get_user_enrolled_courses, name = "extras_get_user_enrolled_courses"),
    re_path(r'^extras/get_last_login', views.extras_get_last_login, name = "extras_get_last_login"),
    re_path(r'^extras/get_payment_details', views.extras_get_payment_details, name = "extras_get_payment_details"),
    re_path(r'^extras/cyberstruct_sso$', views.cyberstruct_sso, name = "cyberstruct_sso"),

    re_path(r'^email_confirm/(?P<key>[^/]*)$', views.confirm_email_change, name='confirm_email_change'),

    re_path(r'^activate/(?P<key>[^/]*)$', views.activate_account, name="activate"),

    re_path(r'^extras/join_lens_meeting$', views.join_lens_meeting, name = "join_lens_meeting"),

    path('accounts/disable_account_ajax', views.disable_account_ajax, name="disable_account_ajax"),
    path('accounts/manage_user_standing', views.manage_user_standing, name='manage_user_standing'),

    path('api/change_email_settings', views.change_email_settings, name='change_email_settings'),

    re_path(fr'^course_run/{settings.COURSE_ID_PATTERN}/refund_status$',
            views.course_run_refund_status,
            name="course_run_refund_status"),

    re_path(
        r'^activate_secondary_email/(?P<key>[^/]*)$',
        views.activate_secondary_email,
        name='activate_secondary_email'
    ),
]


urlpatterns += [re_path(r'^assessment_tracker', views.user_tracker_link, name='user_tracker_link')]
