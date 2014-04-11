"""Auth pipeline definitions.

Auth pipelines handle the process of authenticating a user. They involve a
consumer system and a provider service. The general pattern is:

    1. The consumer system exposes a URL endpoint that starts the process.
    2. When a user visits that URL, the client system redirects the user to a
       page served by the provider. The user authenticates with the provider.
       The provider handles authentication failure however it wants.
    3. On success, the provider POSTs to a URL endpoint on the consumer to
       invoke the pipeline. It sends back an arbitrary payload of data about
       the user.
    4. The pipeline begins, executing each function in its stack. The stack is
       defined on django's settings object's SOCIAL_AUTH_PIPELINE. This is done
       in settings._set_global_settings.
    5. Each pipeline function is variadic. Most pipeline functions are part of
       the pythons-social-auth library; our extensions are defined below. The
       pipeline is the same no matter what provider is used.
    6. Pipeline functions can return a dict to add arguments to the function
       invoked next. They can return None if this is not necessary.
    7. Pipeline functions may be decorated with @partial.partial. This pauses
       the pipeline and serializes its state onto the request's session. When
       this is done they may redirect to other edX handlers to execute edX
       account registration/sign in code.
    8. In that code, redirecting to get_complete_url() resumes the pipeline.
       This happens by hitting a handler exposed by the consumer system.
    9. In this way, execution moves between the provider, the pipeline, and
       arbitrary consumer system code.

Gotcha alert!:

Bear in mind that when pausing and resuming a pipeline function decorated with
@partial.partial, execution resumes by re-invoking the decorated function
instead of invoking the next function in the pipeline stack. For example, if
you have a pipeline of

    A
    B
    C

with an implementation of

    @partial.partial
    def B(*args, **kwargs):
        [...]

B will be invoked twice: once when initially proceeding through the pipeline
before it is paused, and once when other code finishes and the pipeline
resumes. Consequently, many decorated functions will first invoke a predicate
to determine if they are in their first or second execution (usually by
checking side-effects from the first run).

This is surprising but important behavior, since it allows a single function in
the pipeline to consolidate all the operations needed to establish invariants
rather than spreading them across two functions in the pipeline.

See http://psa.matiasaguirre.net/docs/pipeline.html for more docs.
"""

import random
import string  # pylint: disable-msg=deprecated-module

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from social.apps.django_app.default import models
from social.exceptions import AuthException
from social.pipeline import partial

from . import provider


AUTH_ENTRY_KEY = 'auth_entry'
AUTH_ENTRY_LOGIN = 'login'
AUTH_ENTRY_REGISTER = 'register'
_AUTH_ENTRY_CHOICES = frozenset([AUTH_ENTRY_LOGIN, AUTH_ENTRY_REGISTER])
_DEFAULT_RANDOM_PASSWORD_LENGTH = 12
_PASSWORD_CHARSET = string.letters + string.digits


class AuthEntryError(AuthException):
    """Raised when auth_entry is missing or invalid on URLs.

    auth_entry tells us whether the auth flow was initiated to register a new
    user (in which case it has the value of AUTH_ENTRY_REGISTER) or log in an
    existing user (in which case it has the value of AUTH_ENTRY_LOGIN).

    This is necessary because the edX code we hook into the pipeline to
    redirect to the existing auth flows needs to know what case we are in in
    order to format its output correctly (for example, the register code is
    invoked earlier than the login code, and it needs to know if the login flow
    was requested to dispatch correctly).
    """


def get(request):
    """Gets the running pipeline from the passed request."""
    return request.session.get('partial_pipeline')


def get_authenticated_user(username, backend_name):
    """Gets a saved user authenticated by a particular backend.

    Between pipeline steps User objects are not saved. We need to reconstitute
    the user and set its .backend, which is ordinarily monkey-patched on by
    Django during authenticate(), so it will function like a user returned by
    authenticate().

    Args:
        username: string. Username of user to get.
        backend_name: string. The name of the third-party auth backend from
            the running pipeline.

    Returns:
        User if user is found and has a social auth from the passed
        backend_name.

    Raises:
        User.DoesNotExist: if no user matching user is found, or the matching
        user has no social auth associated with the given backend.
        AssertionError: if the user is not authenticated.
    """
    user = models.DjangoStorage.user.user_model().objects.get(username=username)

    if not user:
        raise User.DoesNotExist

    match = models.DjangoStorage.user.get_social_auth_for_user(user, provider=backend_name)

    if not match:
        raise User.DoesNotExist

    user.backend = provider.Registry.get_by_backend_name(backend_name).get_authentication_backend()
    return user


def _get_url(view_name, backend_name, auth_entry=None):
    """Creates a URL to hook into social auth endpoints."""
    kwargs = {'backend': backend_name}
    url = reverse(view_name, kwargs=kwargs)

    if auth_entry:
        url += '?%s=%s' % (AUTH_ENTRY_KEY, auth_entry)

    return url


def get_complete_url(backend_name):
    """Gets URL for the endpoint that returns control to the auth pipeline.

    Args:
        backend_name: string. Name of the python-social-auth backend from the
            currently-running pipeline.

    Returns:
        String. URL that finishes the auth pipeline for a provider.

    Raises:
        ValueError: if no provider is enabled with the given backend_name.
    """
    enabled_provider = provider.Registry.get_by_backend_name(backend_name)

    if not enabled_provider:
        raise ValueError('Provider with backend %s not enabled' % backend_name)

    return _get_url('social:complete', backend_name)


def get_login_url(provider_name, auth_entry):
    """Gets the login URL for the endpoint that kicks off auth with a provider.

    Args:
        provider_name: string. The name of the provider.Provider that has been
            enabled.
        auth_entry: string. Query argument specifying the desired entry point
            for the auth pipeline. Used by the pipeline for later branching.
            Must be one of _AUTH_ENTRY_CHOICES.

    Returns:
        String. URL that starts the auth pipeline for a provider.

    Raises:
        ValueError: if no provider is enabled with the given provider_name.
    """
    assert auth_entry in _AUTH_ENTRY_CHOICES
    enabled_provider = provider.Registry.get(provider_name)

    if not enabled_provider:
        raise ValueError('Provider %s not enabled' % provider_name)

    return _get_url('social:begin', enabled_provider.BACKEND_CLASS.name, auth_entry=auth_entry)


def make_random_password(length=None, choice_fn=random.SystemRandom().choice):
    """Makes a random password.

    When a user creates an account via a social provider, we need to create a
    placeholder password for them to satisfy the ORM's consistency and
    validation requirements. Users don't know (and hence cannot sign in with)
    this password; that's OK because they can always use the reset password
    flow to set it to a known value.

    Args:
        choice_fn: function or method. Takes an iterable and returns a random
            element.
        length: int. Number of chars in the returned value. None to use default.

    Returns:
        String. The resulting password.
    """
    length = length if length is not None else _DEFAULT_RANDOM_PASSWORD_LENGTH
    return ''.join(choice_fn(_PASSWORD_CHARSET) for _ in xrange(length))


def running(request):
    """Returns True iff request is running a third-party auth pipeline."""
    return request.session.get('partial_pipeline') is not None  # Avoid False for {}.


# Pipeline functions.
# Signatures are set by python-social-auth; prepending 'unused_' causes
# TypeError on dispatch to the auth backend's authenticate().
# pylint: disable-msg=unused-argument


def parse_query_params(strategy, response, *args, **kwargs):
    """Reads whitelisted query params, transforms them into pipeline args."""
    auth_entry = strategy.session.get(AUTH_ENTRY_KEY)

    if not (auth_entry and auth_entry in _AUTH_ENTRY_CHOICES):
        raise AuthEntryError(strategy.backend, 'auth_entry missing or invalid')

    return {
        # Whether the auth pipeline entered from /login.
        'is_login': auth_entry == AUTH_ENTRY_LOGIN,
        # Whether the auth pipeline entered from /register.
        'is_register': auth_entry == AUTH_ENTRY_REGISTER,
    }


@partial.partial
def redirect_to_supplementary_form(strategy, details, response, uid, is_login=None, is_register=None, user=None, *args, **kwargs):
    """Dispatches user to a create account form if they are new."""
    if is_login:
        return redirect('/login', name='signin_user')

    if is_register and user is None:
        return redirect('/register', name='register_user')
