"""
URLs for student app
"""

from django.conf import settings
from django.conf.urls import url
from django.contrib.auth.views import password_reset_complete

import student.views

urlpatterns = [
    url(r'^logout$', student.views.LogoutView.as_view(), name='logout'),

    # TODO: standardize login

    # login endpoint used by cms.
    url(r'^login_post$', student.views.login_user, name='login_post'),
    # login endpoints used by lms.
    url(r'^login_ajax$', student.views.login_user, name="login"),
    url(r'^login_ajax/(?P<error>[^/]*)$', student.views.login_user),

    url(r'^email_confirm/(?P<key>[^/]*)$', student.views.confirm_email_change, name='confirm_email_change'),

    url(r'^create_account$', student.views.create_account, name='create_account'),
    url(r'^activate/(?P<key>[^/]*)$', student.views.activate_account, name="activate"),

    url(r'^accounts/disable_account_ajax$', student.views.disable_account_ajax, name="disable_account_ajax"),
    url(r'^accounts/manage_user_standing', student.views.manage_user_standing, name='manage_user_standing'),

    url(r'^change_setting$', student.views.change_setting, name='change_setting'),
    url(r'^change_email_settings$', student.views.change_email_settings, name='change_email_settings'),

    # password reset in student.views (see below for password reset django views)
    url(r'^password_reset/$', student.views.password_reset, name='password_reset'),
    url(
        r'^password_reset_confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
        student.views.password_reset_confirm_wrapper,
        name='password_reset_confirm',
    ),
    url(r'^course_run/{}/refund_status$'.format(settings.COURSE_ID_PATTERN),
        student.views.course_run_refund_status,
        name="course_run_refund_status"),

]

# enable automatic login
if settings.FEATURES.get('AUTOMATIC_AUTH_FOR_TESTING'):
    urlpatterns += [
        url(r'^auto_auth$', student.views.auto_auth),
    ]

# password reset django views (see above for password reset student.views)
urlpatterns += [
    # TODO: Replace with Mako-ized views
    url(
        r'^password_reset_complete/$',
        password_reset_complete,
        name='password_reset_complete',
    ),
]
