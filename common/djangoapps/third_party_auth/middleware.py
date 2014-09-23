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
from . import portal

log = logging.getLogger(__file__)

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
        if request.user.is_authenticated():
            user = request.user
            social_auth = models.DjangoStorage.user.get_social_auth_for_user(user)

            if len(social_auth) == 1:
                social_data = social_auth[0]

                try:
                    r = requests.get(
                        settings.IONISX_AUTH.get('USER_DATA_URL'),
                        headers={'Authorization': 'Bearer {0}'.format(social_data.extra_data['access_token'])}
                    )
                except requests.ConnectionError as err:
                    log.warning(err)
                    return

                user_data = r.json()
                if user_data:
                    _id = user_data['_id']
                    email = portal.get_primary_email(user_data['emails'])
                    username = user_data['username']
                    name = user_data['name']

                    if (user.email != email or user.username != user_data['username']):
                        log.info('User {} needs to be updated'.format(_id))
                        user.email = email
                        user.username = username
                        user.save()

                    if user.profile.name != user_data['name']:
                        log.info('User profile for {} needs to be updated'.format(_id))
                        user.profile.name = name
                        user.profile.save()
