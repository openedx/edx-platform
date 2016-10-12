"""
URLs for student app
"""

from django.conf import settings
from django.conf.urls import patterns, url

from student.views import LogoutView

urlpatterns = (
    'student.views',

    url(r'^logout$', LogoutView.as_view(), name='logout'),

    # TODO: standardize login

    # login endpoint used by cms.
    url(r'^login_post$', 'login_user', name='login_post'),
    # login endpoints used by lms.
    url(r'^login_ajax$', 'login_user', name="login"),
    url(r'^login_ajax/(?P<error>[^/]*)$', 'login_user'),

    url(r'^email_confirm/(?P<key>[^/]*)$', 'confirm_email_change'),

    url(r'^create_account$', 'create_account', name='create_account'),
    url(r'^activate/(?P<key>[^/]*)$', 'activate_account', name="activate"),

    url(r'^accounts/disable_account_ajax$', 'disable_account_ajax', name="disable_account_ajax"),
    url(r'^accounts/manage_user_standing', 'manage_user_standing', name='manage_user_standing'),

    url(r'^change_setting$', 'change_setting', name='change_setting'),
    url(r'^change_email_settings$', 'change_email_settings', name='change_email_settings'),
)

# enable automatic login
if settings.FEATURES.get('AUTOMATIC_AUTH_FOR_TESTING'):
    urlpatterns += (
        url(r'^auto_auth$', 'auto_auth'),
    )

urlpatterns = patterns(*urlpatterns)

# password reset mixes student.views with django views
urlpatterns += (
    url(r'^password_reset/$', 'student.views.password_reset', name='password_reset'),

    # Obsolete Django views for password resets

    # TODO: Replace with Mako-ized views

    url(r'^password_change/$', 'django.contrib.auth.views.password_change', name='password_change'),
    url(r'^password_change_done/$', 'django.contrib.auth.views.password_change_done', name='password_change_done'),
    url(
        r'^password_reset_complete/$',
        'django.contrib.auth.views.password_reset_complete',
        name='password_reset_complete',
    ),
    url(
        r'^password_reset_confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
        'student.views.password_reset_confirm_wrapper',
        name='password_reset_confirm',
    ),
    url(r'^password_reset_done/$', 'django.contrib.auth.views.password_reset_done', name='password_reset_done'),
)
