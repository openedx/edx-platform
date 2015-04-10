# pylint: disable=E1101

""" API implementation for session-oriented interactions. """
import logging

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY, load_backend
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import ObjectDoesNotExist
from django.utils.importlib import import_module
from django.utils.translation import ugettext as _
from api_manager.permissions import SecureAPIView
from rest_framework import status
from rest_framework.response import Response
from django.utils import timezone
from django.template import RequestContext


from util.bad_request_rate_limiter import BadRequestRateLimiter
from api_manager.utils import generate_base_uri

from api_manager.users.serializers import UserSerializer
from student.models import (
    LoginFailures, PasswordHistory
)
AUDIT_LOG = logging.getLogger("audit")


class SessionsList(SecureAPIView):
    """
    **Use Case**

        SessionsList creates a new session with the edX LMS.

    **Example Request**

        POST  {"username": "staff", "password": "edx"}

    **Response Values**

        * token: A unique token value for the session created.
        * expires: The number of seconds until the new session expires.
        * user: The following data about the user for whom the session is
          created.
            * id: The unique user identifier.
            * email: The user's email address.
            * username: The user's edX username.
            * first_name: The user's first name, if defined.
            * last_name: The user's last name, if defined.
            * creaed:  The time and date the user account was created.
            * organizations: An array of organizations the user is associated
              with.
        * uri: The URI to use to get details about the new session.
    """

    def post(self, request):
        response_data = {}
        # Add some rate limiting here by re-using the RateLimitMixin as a helper class
        limiter = BadRequestRateLimiter()
        if limiter.is_rate_limit_exceeded(request):
            response_data['message'] = _('Rate limit exceeded in api login.')
            return Response(response_data, status=status.HTTP_403_FORBIDDEN)

        base_uri = generate_base_uri(request)
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
                    #
                    # Create a new session directly with the SESSION_ENGINE
                    # We don't call the django.contrib.auth login() method
                    # because it is bound with the HTTP request.
                    #
                    # Since we are a server-to-server API, we shouldn't
                    # be stateful with respect to the HTTP request
                    # and anything that might come with it, as it could
                    # violate our RESTfulness
                    #
                    engine = import_module(settings.SESSION_ENGINE)
                    new_session = engine.SessionStore()
                    new_session.create()

                    # These values are expected to be set in any new session
                    new_session[SESSION_KEY] = user.id
                    new_session[BACKEND_SESSION_KEY] = user.backend

                    new_session.save()

                    response_data['token'] = new_session.session_key
                    response_data['expires'] = new_session.get_expiry_age()
                    user_dto = UserSerializer(user)
                    response_data['user'] = user_dto.data
                    response_data['uri'] = '{}/{}'.format(base_uri, new_session.session_key)
                    response_status = status.HTTP_201_CREATED

                    # generate a CSRF tokens for any web clients that may need to
                    # call into the LMS via Ajax (for example Notifications)
                    response_data['csrftoken'] = RequestContext(request, {}).get('csrf_token')

                    # update the last_login fields in the auth_user table for this user
                    user.last_login = timezone.now()
                    user.save()

                    # add to audit log
                    AUDIT_LOG.info(u"API::User logged in successfully with user-id - {0}".format(user.id))
                else:
                    response_status = status.HTTP_403_FORBIDDEN
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


class SessionsDetail(SecureAPIView):
    """
    **Use Case**

        SessionsDetail gets a details about a specific API session, as well as
        enables you to delete an API session.


    **Example Requests**

        GET /api/session/{session_id}

        DELETE /api/session/{session_id}/delete

    **GET Response Values**

        * token: A unique token value for the session.
        * expires: The number of seconds until the session expires.
        * user_id: The unique user identifier.
        * uri: The URI to use to get details about the session.
    """

    def get(self, request, session_id):
        response_data = {}
        base_uri = generate_base_uri(request)
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
        engine = import_module(settings.SESSION_ENGINE)
        session = engine.SessionStore(session_id)
        if session is None or not SESSION_KEY in session:
            return Response({}, status=status.HTTP_204_NO_CONTENT)
        user_id = session[SESSION_KEY]
        session.delete()

        AUDIT_LOG.info(u"API::User session terminated for user-id - {0}".format(user_id))
        return Response({}, status=status.HTTP_204_NO_CONTENT)
