"""
General testing utilities.
"""


import functools
import sys
from contextlib import contextmanager

import pytest
from django.dispatch import Signal
from markupsafe import escape
from mock import Mock, patch


@contextmanager
def nostderr():
    """
    ContextManager to suppress stderr messages
    http://stackoverflow.com/a/1810086/882918
    """
    savestderr = sys.stderr

    class Devnull(object):
        """ /dev/null incarnation as output-stream-like object """
        def write(self, _):
            """ Write method - just does nothing"""
            pass

    sys.stderr = Devnull()
    try:
        yield
    finally:
        sys.stderr = savestderr


class XssTestMixin(object):
    """
    Mixin for testing XSS vulnerabilities.
    """

    def assert_no_xss(self, response, xss_content):
        """Assert that `xss_content` is not present in the content of
        `response`, and that its escaped version is present. Uses the
        same `markupsafe.escape` function as Mako templates.

        Args:
          response (Response): The HTTP response
          xss_content (str): The Javascript code to check for.

        Returns:
          None

        """
        self.assertContains(response, escape(xss_content))
        self.assertNotContains(response, xss_content)


def disable_signal(module, signal):
    """Replace `signal` inside of `module` with a dummy signal. Can be
    used as a method or class decorator, as well as a context manager."""
    return patch.object(module, signal, new=Signal())


class MockSignalHandlerMixin(object):
    """Mixin for testing sending of signals."""

    @contextmanager
    def assert_signal_sent(self, module, signal, *args, **kwargs):
        """Assert that a signal was sent with the correct arguments. Since
        Django calls signal handlers with the signal as an argument,
        it is added to `kwargs`.

        Uses `mock.patch.object`, which requires the target to be
        specified as a module along with a variable name inside that
        module.

        Args:
          module (module): The module in which to patch the given signal name.
          signal (str): The name of the signal to patch.
          *args, **kwargs: The arguments which should have been passed
            along with the signal. If `exclude_args` is passed as a
            keyword argument, its value should be a list of keyword
            arguments passed to the signal whose values should be
            ignored.

        """
        with patch.object(module, signal, new=Signal()) as mock_signal:
            def handler(*args, **kwargs):  # pylint: disable=unused-argument
                """No-op signal handler."""
                pass
            mock_handler = Mock(spec=handler)
            mock_signal.connect(mock_handler)
            yield
            self.assertTrue(mock_handler.called)
            mock_args, mock_kwargs = mock_handler.call_args
            if 'exclude_args' in kwargs:
                for key in kwargs['exclude_args']:
                    self.assertIn(key, mock_kwargs)
                    del mock_kwargs[key]
                del kwargs['exclude_args']
            self.assertEqual(mock_args, args)
            self.assertEqual(mock_kwargs, dict(kwargs, signal=mock_signal))


@contextmanager
def skip_signal(signal, **kwargs):
    """
    ContextManager to skip a signal by disconnecting it, yielding,
    and then reconnecting the signal.
    """
    signal.disconnect(**kwargs)
    try:
        yield
    finally:
        signal.connect(**kwargs)


class MockS3BotoMixin(object):
    """
    TestCase mixin that mocks the S3BotoStorage save method and s3 connection.
    """
    def setUp(self):
        super(MockS3BotoMixin, self).setUp()
        self._mocked_connection = patch('boto.connect_s3', return_value=Mock())
        self.mocked_connection = self._mocked_connection.start()

        self.patcher = patch('storages.backends.s3boto.S3BotoStorage.save')
        self.patcher.start()

    def tearDown(self):
        self._mocked_connection.stop()
        self.patcher.stop()
        super(MockS3BotoMixin, self).tearDown()


class reprwrapper(object):
    """
    Wrapper class for functions that need a normalized string representation.
    """
    def __init__(self, func):
        self._func = func
        self.repr = u'Func: {}'.format(func.__name__)
        functools.update_wrapper(self, func)

    def __call__(self, *args, **kw):
        return self._func(*args, **kw)

    def __repr__(self):
        return self.repr


def normalize_repr(func):
    """
    Function decorator used to normalize its string representation.
    Used to wrap functions used as ddt parameters, so pytest-xdist
    doesn't complain about the sequence of discovered tests differing
    between worker processes.
    """
    return reprwrapper(func)


# Decorator for skipping tests that are not ready to be run with Python 3.x.
# While we expect many tests to fail with Python 3.x as we transition, this
# is specifically for tests that rely on external or large scale fixes. It can
# be added to individual tests or test classes.
py2_only = pytest.mark.skipif(
    sys.version_info > (3, 0),
    reason="This test can only be run with Python 2.7, currently"
)
