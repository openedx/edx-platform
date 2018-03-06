from django.conf.urls import patterns, url
from django.conf import settings

urlpatterns = []

if settings.FEATURES.get('ENABLE_COMBINED_LOGIN_REGISTRATION'):
    urlpatterns += patterns(
        'student_account.views',
        url(r'^password$', 'password_change_request_handler', name='password_change_request'),
    )

urlpatterns += patterns(
    'student_account.views',
    url(r'^finish_auth$', 'finish_auth', name='finish_auth'),
    url(r'^settings$', 'account_settings', name='account_settings'),
    url(r'^get_cookies$', 'cookies_api', name='cookies_api'),
    url(r'^link$', 'link_account', name='link_account'),
    url(r'^link/confirm$', 'link_account_confirm', name='link_account_confirm')
)
