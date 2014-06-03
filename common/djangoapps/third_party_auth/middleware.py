"""Middleware classes for third_party_auth."""

import logging
import requests

from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib.auth.models import AnonymousUser
from student.models import UserProfile

from social.apps.django_app.default import models
from social.apps.django_app.middleware import SocialAuthExceptionMiddleware

from . import pipeline

log = logging.getLogger('third_party_auth.middleware')

class ExceptionMiddleware(SocialAuthExceptionMiddleware):
    """Custom middleware that handles conditional redirection."""

    def get_redirect_uri(self, request, exception):
        # Safe because it's already been validated by
        # pipeline.parse_query_params. If that pipeline step ever moves later
        # in the pipeline stack, we'd need to validate this value because it
        # would be an injection point for attacker data.
        auth_entry = request.session.get(pipeline.AUTH_ENTRY_KEY)
        # Fall back to django settings's SOCIAL_AUTH_LOGIN_ERROR_URL.
        return '/' + auth_entry if auth_entry else super(ExceptionMiddleware, self).get_redirect_uri(request, exception)

class PortalSynchronizerMiddleware(object):
    """Custom middleware to synchronize user status of LMS with Portal provider."""

    def process_request(self, request):
        if not isinstance(request.user, AnonymousUser):
            try:
                email = request.user.email
                user = models.DjangoStorage.user.objects.get(uid=email)
                response = requests.request('POST', settings.IONISX_AUTH['SYNC_USER_URL'],
                                    params={ 'access_token': user.extra_data['access_token'] })
                response = response.json()
                if response is None:
                    logout(request)
                    response = redirect(request.get_full_path())
                    response.delete_cookie(
                        settings.EDXMKTG_COOKIE_NAME,
                        path='/', domain=settings.SESSION_COOKIE_DOMAIN,
                    )
                    return response
                if response['updated'] is True:
                    log.warning('need update !')
                    user = request.user
                    user.email = response['emails'][0]['email']
                    user.username = response['username']
                    user.save()

                    profile = UserProfile.objects.get(user=request.user)
                    profile.name = response['name']
                    profile.save()
            except requests.ConnectionError as err:
                log.warning(err)
            except Exception as err:
                log.warning(err)
