from django.conf.urls import patterns, url
from django.conf import settings


urlpatterns = patterns(
    'student_account.views',
    url(r'^login/$', 'login_and_registration_form', {'initial_mode': 'login'}, name='login'),
    url(r'^register/$', 'login_and_registration_form', {'initial_mode': 'register'}, name='register'),
)

if settings.FEATURES.get('ENABLE_NEW_DASHBOARD'):
    urlpatterns += patterns(
        'student_account.views',
        url(r'^$', 'index', name='account_index'),
        url(r'^email$', 'email_change_request_handler', name='email_change_request'),
        url(r'^email/confirmation/(?P<key>[^/]*)$', 'email_change_confirmation_handler', name='email_change_confirm'),
    )