""" URLs for User Authentication """
from django.conf import settings
from django.conf.urls import include, url

from openedx.core.djangoapps.user_api.accounts import settings_views
from .views import login_form, login, deprecated


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
        url(r'^login$', login_form.login_and_registration_form,
            {'initial_mode': 'login'}, name='signin_user'),
        url(r'^register$', login_form.login_and_registration_form,
            {'initial_mode': 'register'}, name='register_user'),
    ]
else:
    # Serve the old views
    urlpatterns += [
        url(r'^login$', deprecated.signin_user, name='signin_user'),
        url(r'^register$', deprecated.register_user, name='register_user'),
    ]
