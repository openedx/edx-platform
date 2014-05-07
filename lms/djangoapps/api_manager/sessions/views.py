# pylint: disable=E1101

""" API implementation for session-oriented interactions. """
import logging

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY, load_backend
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import ObjectDoesNotExist
from django.utils.importlib import import_module
from django.utils.translation import ugettext as _

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from util.bad_request_rate_limiter import BadRequestRateLimiter

from api_manager.permissions import ApiKeyHeaderPermission
from api_manager.users.serializers import UserSerializer
from student.models import (
    LoginFailures, PasswordHistory
)
AUDIT_LOG = logging.getLogger("audit")


def _generate_base_uri(request):
    """
    Constructs the protocol:host:path component of the resource uri
    """
    protocol = 'http'
    if request.is_secure():
        protocol = protocol + 's'
    resource_uri = '{}://{}{}'.format(
        protocol,
        request.get_host(),
        request.get_full_path()
    )
    return resource_uri


class SessionsList(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def post(self, request):
        """
        POST creates a new system session, supported authentication modes:
        1. Open edX username/password
        """
        response_data = {}
        # Add some rate limiting here by re-using the RateLimitMixin as a helper class
        limiter = BadRequestRateLimiter()
        if limiter.is_rate_limit_exceeded(request):
            response_data['message'] = _('Rate limit exceeded in api login.')
            return Response(response_data, status=status.HTTP_403_FORBIDDEN)

        base_uri = _generate_base_uri(request)
        try:
            existing_user = User.objects.get(username=request.DATA['username'])
        except ObjectDoesNotExist:
            existing_user = None

        # see if account has been locked out due to excessive login failures
        if existing_user and LoginFailures.is_feature_enabled():
            if LoginFailures.is_user_locked_out(existing_user):
                response_status = status.HTTP_403_FORBIDDEN
                response_data['message'] = _('This account has been temporarily locked due to excessive login failures. '
                                             'Try again later.')
                return Response(response_data, status=response_status)

         # see if the user must reset his/her password due to any policy settings
        if existing_user and PasswordHistory.should_user_reset_password_now(existing_user):
            response_status = status.HTTP_403_FORBIDDEN
            response_data['message'] = _(
                'Your password has expired due to password policy on this account. '
                'You must reset your password before you can log in again.'
            )
            return Response(response_data, status=response_status)

        if existing_user:
            user = authenticate(username=existing_user.username, password=request.DATA['password'])
            if user is not None:

                # successful login, clear failed login attempts counters, if applicable
                if LoginFailures.is_feature_enabled():
                    LoginFailures.clear_lockout_counter(user)

                if user.is_active:
                    login(request, user)
                    response_data['token'] = request.session.session_key
                    response_data['expires'] = request.session.get_expiry_age()
                    user_dto = UserSerializer(user)
                    response_data['user'] = user_dto.data
                    response_data['uri'] = '{}/{}'.format(base_uri, request.session.session_key)
                    response_status = status.HTTP_201_CREATED

                    # add to audit log
                    AUDIT_LOG.info(u"API::User logged in successfully with user-id - {0}".format(user.id))
                else:
                    response_status = status.HTTP_401_UNAUTHORIZED
            else:
                limiter.tick_bad_request_counter(request)
                # tick the failed login counters if the user exists in the database
                if LoginFailures.is_feature_enabled():
                    LoginFailures.increment_lockout_counter(existing_user)

                response_status = status.HTTP_401_UNAUTHORIZED
                AUDIT_LOG.warn(u"API::User authentication failed with user-id - {0}".format(existing_user.id))
        else:
            AUDIT_LOG.warn(u"API::Failed login attempt with unknown email/username")
            response_status = status.HTTP_404_NOT_FOUND
        return Response(response_data, status=response_status)


class SessionsDetail(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def get(self, request, session_id):
        """
        GET retrieves an existing system session
        """
        response_data = {}
        base_uri = _generate_base_uri(request)
        engine = import_module(settings.SESSION_ENGINE)
        session = engine.SessionStore(session_id)
        try:
            user_id = session[SESSION_KEY]
            backend_path = session[BACKEND_SESSION_KEY]
            backend = load_backend(backend_path)
            user = backend.get_user(user_id) or AnonymousUser()
        except KeyError:
            user = AnonymousUser()
        if user.is_authenticated():
            response_data['token'] = session.session_key
            response_data['expires'] = session.get_expiry_age()
            response_data['uri'] = base_uri
            response_data['user_id'] = user.id
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, session_id):
        """
        DELETE flushes an existing system session from the system
        """
        response_data = {}
        base_uri = _generate_base_uri(request)
        engine = import_module(settings.SESSION_ENGINE)
        session = engine.SessionStore(session_id)
        user_id = session[SESSION_KEY]
        AUDIT_LOG.info(u"API::User session terminated for user-id - {0}".format(user_id))
        session.flush()
        logout(request)
        return Response(response_data, status=status.HTTP_204_NO_CONTENT)
