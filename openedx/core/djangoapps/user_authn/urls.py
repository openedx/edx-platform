""" URLs for User Authentication """
from django.conf import settings
from django.conf.urls import include, url

from openedx.core.djangoapps.user_api.accounts import settings_views
from openedx.features.student_account.views import login_and_registration_form as\
    login_and_registration_form_v2

from lms.djangoapps.philu_overrides.views import login_and_registration_form

from .views import login, deprecated


urlpatterns = [
    # TODO this should really be declared in the user_api app
    url(r'^account/settings$', settings_views.account_settings, name='account_settings'),

    # TODO move contents of urls_common here once CMS no longer has its own login
    url(r'', include('openedx.core.djangoapps.user_authn.urls_common')),
    url(r'^account/finish_auth$', login.finish_auth, name='finish_auth'),
]


if settings.FEATURES.get('ENABLE_COMBINED_LOGIN_REGISTRATION'):
    # Backwards compatibility with old URL structure, but serve the new views
    urlpatterns += [
        url(r'^login$', login_and_registration_form,
            {'initial_mode': 'login'}, name="signin_user"),
        url(r'^register$', login_and_registration_form,
            {'initial_mode': 'register'}, name="register_user"),
        url(r'^signup', login_and_registration_form_v2,
            {'initial_mode': 'register'}, name="register_user"),
        url(r'^register/(?P<org_name>[^/]*)/(?P<admin_email>[^/]*)/$',
            login_and_registration_form,
            {'initial_mode': 'register'}, name="register_user"),
    ]
else:
    # Serve the old views
    urlpatterns += [
        url(r'^login$', deprecated.signin_user, name='signin_user'),
        url(r'^register$', deprecated.register_user, name='register_user'),
    ]
