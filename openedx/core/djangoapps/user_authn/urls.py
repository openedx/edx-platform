""" URLs for User Authentication """

from django.conf.urls import include, url

from .views import login, login_form

urlpatterns = [
    # TODO move contents of urls_common here once CMS no longer has its own login
    url(r'', include('openedx.core.djangoapps.user_authn.urls_common')),
    url(r'^api/', include('openedx.core.djangoapps.user_authn.api.urls')),
    url(r'^account/finish_auth$', login.finish_auth, name='finish_auth'),
]


# Backwards compatibility with old URL structure, but serve the new views
urlpatterns += [
    url(r'^login$', login_form.login_and_registration_form,
        {'initial_mode': 'login'}, name='signin_user'),
    url(r'^register$', login_form.login_and_registration_form,
        {'initial_mode': 'register'}, name='register_user'),
    url(r'^password_assistance', login_form.login_and_registration_form,
        {'initial_mode': 'reset'}, name='password_assistance'),
]
