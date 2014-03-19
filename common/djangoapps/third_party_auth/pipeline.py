"""Auth pipeline definitions.

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
before it is paused, and and once when other code finishes and the pipeline
resumes. Consequently, many decorated functions will first invoke a predicate
to determine if they are in their first or second execution (usually by
checking side-effects from the first run).

This is surprising but important behavior, since it allows a single function in
the pipeline to consolidate all the operations needed to establish invariants
rather than spreading them across two functions in the pipeline.

See http://psa.matiasaguirre.net/docs/pipeline.html for more docs.
"""

import random
# string is deprecated, but it's still the surest way to get these charsets.
# pylint: disable-msg=deprecated-module
import string

from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from social.pipeline import partial

from . import provider


# Int. Default size for randomly-generated passwords.
_DEFAULT_RANDOM_PASSWORD_LENGTH = 12
# String. The characters available to the random password generator. Must pass
# the ORM's validation routines.
_PASSWORD_CHARSET = string.letters + string.digits


def get(request):
    """Gets the running pipeline from `request`."""
    return request.session.get('partial_pipeline')


def _get_url(view_name, backend_name):
    """Protected wrapper for reverse()."""
    return reverse(view_name, kwargs={'backend': backend_name})


def get_complete_url(backend_name):
    """Gets URL for the endpoint that returns control to the auth pipeline.

    Arg is `backend_name`, the name of the python-social-auth backend from the
    running pipeline (for example, 'google-oauth2'). Returns string.
    """
    return _get_url('social:complete', backend_name)


def get_login_url(provider_name):
    """Gets the login URL for the endpoint that kicks of auth with a provider.

    Args are `provider_name`, a string containing the name of a
    provider.Provider that has been enabled. Returns string.
    """
    enabled_provider = provider.Registry.get(provider_name)
    if not enabled_provider:
        raise ValueError('Provider %s not enabled' % provider_name)
    return _get_url('social:begin', enabled_provider.BACKEND_CLASS.name)


def make_random_password(length=None, seed=None):
    """Makes a random password.

    When a user creates an account via a social provider, we need to create a
    placeholder password for them to satisfy the ORM's consistency and
    validation requirements. Users don't know (and hence cannot sign in with)
    this password; that's OK because they can always use the reset password
    flow to set it to a known value.

    Args are `length`, an int that determines the number of chars in the
    returned value, and `seed`, a hashable object used to initialize the RNG.
    `seed` is for tests only; do not pass it otherwise.
    """
    if length is None:
        length = _DEFAULT_RANDOM_PASSWORD_LENGTH

    if seed is not None:
        random.seed(seed)

    return ''.join(random.choice(_PASSWORD_CHARSET) for _ in xrange(length))


def running(request):
    """Returns True iff `request` is running a third-party auth pipeline."""
    return request.session.get('partial_pipeline') is not None  # Avoid False for {}.


# Signature set by framework; prepending 'unused_' causes TypeError on dispatch
# to the auth backend's authenticate(). pylint: disable-msg=unused-argument
@partial.partial
def redirect_to_supplementary_form(strategy, details, response, uid, user=None, *args, **kwargs):
    """Cut point that dispatches user to a create account or sign in form."""
    if user is not None:
        return

    return redirect('/register', name='register_user')
