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
    re_path(r'^extras/attendance$', views.extras_get_attendance, name = "extras_get_attendance"),

    re_path(r'^extras/reset_password_link', views.extras_reset_password_link, name = "extras_reset_password_link"),

    re_path(r'^email_confirm/(?P<key>[^/]*)$', views.confirm_email_change, name='confirm_email_change'),

    re_path(r'^activate/(?P<key>[^/]*)$', views.activate_account, name="activate"),

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
