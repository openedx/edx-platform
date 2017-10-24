from django.conf import settings
from django.conf.urls import url

from student_account.views import password_change_request_handler, finish_auth, account_settings

urlpatterns = [
    url(r'^finish_auth$', finish_auth, name='finish_auth'),
    url(r'^settings$', account_settings, name='account_settings'),
]

if settings.FEATURES.get('ENABLE_COMBINED_LOGIN_REGISTRATION'):
    urlpatterns += [
        url(r'^password$', password_change_request_handler, name='password_change_request'),
    ]
