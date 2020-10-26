"""
URLs for student app
"""

from django.conf import settings
from django.conf.urls import url
from django.contrib.auth.views import password_reset_complete

from . import views

urlpatterns = [

    url(r'^email_confirm/(?P<key>[^/]*)$', views.confirm_email_change, name='confirm_email_change'),

    url(r'^activate/(?P<key>[^/]*)$', views.activate_account, name="activate"),

    url(r'^accounts/disable_account_ajax$', views.disable_account_ajax, name="disable_account_ajax"),
    url(r'^accounts/manage_user_standing', views.manage_user_standing, name='manage_user_standing'),

    url(r'^change_setting$', views.change_setting, name='change_setting'),
    url(r'^change_email_settings$', views.change_email_settings, name='change_email_settings'),

    # password reset in views (see below for password reset django views)
    url(r'^account/password$', views.password_change_request_handler, name='password_change_request'),
    url(r'^account/account_recovery', views.account_recovery_request_handler, name='account_recovery'),
    url(r'^password_reset/$', views.password_reset, name='password_reset'),
    url(
        r'^password_reset_confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
        views.password_reset_confirm_wrapper,
        name='password_reset_confirm',
    ),
    url(
        r'^account_recovery_confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
        views.account_recovery_confirm_wrapper,
        name='account_recovery_confirm',
    ),

    url(r'^course_run/{}/refund_status$'.format(settings.COURSE_ID_PATTERN),
        views.course_run_refund_status,
        name="course_run_refund_status"),

    url(
        r'^activate_secondary_email/(?P<key>[^/]*)$',
        views.activate_secondary_email,
        name='activate_secondary_email'
    ),

]

# password reset django views (see above for password reset views)
urlpatterns += [
    # TODO: Replace with Mako-ized views
    url(
        r'^password_reset_complete/$',
        password_reset_complete,
        name='password_reset_complete',
    ),
]
