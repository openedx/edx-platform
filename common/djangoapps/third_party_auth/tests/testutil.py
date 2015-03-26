"""
Utilities for writing third_party_auth tests.

Used by Django and non-Django tests; must not have Django deps.
"""

from contextlib import contextmanager
import unittest
import mock

from third_party_auth import provider


AUTH_FEATURES_KEY = 'ENABLE_THIRD_PARTY_AUTH'


class FakeDjangoSettings(object):
    """A fake for Django settings."""

    def __init__(self, mappings):
        """Initializes the fake from mappings dict."""
        for key, value in mappings.iteritems():
            setattr(self, key, value)


class TestCase(unittest.TestCase):
    """Base class for auth test cases."""

    # Allow access to protected methods (or module-protected methods) under
    # test.
    # pylint: disable-msg=protected-access

    def setUp(self):
        super(TestCase, self).setUp()
        self._original_providers = provider.Registry._get_all()
        provider.Registry._reset()

    def tearDown(self):
        provider.Registry._reset()
        provider.Registry.configure_once(self._original_providers)
        super(TestCase, self).tearDown()


@contextmanager
def simulate_running_pipeline(pipeline_target, backend, email=None, fullname=None, username=None):
    """Simulate that a pipeline is currently running.

    You can use this context manager to test packages that rely on third party auth.

    This uses `mock.patch` to override some calls in `third_party_auth.pipeline`,
    so you will need to provide the "target" module *as it is imported*
    in the software under test.  For example, if `foo/bar.py` does this:

    >>> from third_party_auth import pipeline

    then you will need to do something like this:

    >>> with simulate_running_pipeline("foo.bar.pipeline", "google-oauth2"):
    >>>    bar.do_something_with_the_pipeline()

    If, on the other hand, `foo/bar.py` had done this:

    >>> import third_party_auth

    then you would use the target "foo.bar.third_party_auth.pipeline" instead.

    Arguments:

        pipeline_target (string): The path to `third_party_auth.pipeline` as it is imported
            in the software under test.

        backend (string): The name of the backend currently running, for example "google-oauth2".
            Note that this is NOT the same as the name of the *provider*.  See the Python
            social auth documentation for the names of the backends.

    Keyword Arguments:
        email (string): If provided, simulate that the current provider has
            included the user's email address (useful for filling in the registration form).

        fullname (string): If provided, simulate that the current provider has
            included the user's full name (useful for filling in the registration form).

        username (string): If provided, simulate that the pipeline has provided
            this suggested username.  This is something that the `third_party_auth`
            app generates itself and should be available by the time the user
            is authenticating with a third-party provider.

    Returns:
        None

    """
    pipeline_data = {
        "backend": backend,
        "kwargs": {
            "details": {}
        }
    }
    if email is not None:
        pipeline_data["kwargs"]["details"]["email"] = email
    if fullname is not None:
        pipeline_data["kwargs"]["details"]["fullname"] = fullname
    if username is not None:
        pipeline_data["kwargs"]["username"] = username

    pipeline_get = mock.patch("{pipeline}.get".format(pipeline=pipeline_target), spec=True)
    pipeline_running = mock.patch("{pipeline}.running".format(pipeline=pipeline_target), spec=True)

    mock_get = pipeline_get.start()
    mock_running = pipeline_running.start()

    mock_get.return_value = pipeline_data
    mock_running.return_value = True

    try:
        yield

    finally:
        pipeline_get.stop()
        pipeline_running.stop()
