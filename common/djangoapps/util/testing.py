"""
Utility Mixins for unit tests
"""


import json
import sys

import six
from django.conf import settings
from django.test import TestCase
from django.urls import clear_url_caches, resolve
from mock import patch

from common.djangoapps.util.db import OuterAtomic

if six.PY3:
    from importlib import reload


class UrlResetMixin(object):
    """Mixin to reset urls.py before and after a test

    Django memoizes the function that reads the urls module (whatever module
    urlconf names). The module itself is also stored by python in sys.modules.
    To fully reload it, we need to reload the python module, and also clear django's
    cache of the parsed urls.

    However, the order in which we do this doesn't matter, because neither one will
    get reloaded until the next request

    Doing this is expensive, so it should only be added to tests that modify settings
    that affect the contents of urls.py
    """

    URLCONF_MODULES = None

    def reset_urls(self, urlconf_modules=None):
        """Reset `urls.py` for a set of Django apps."""

        if urlconf_modules is None:
            urlconf_modules = [settings.ROOT_URLCONF]
            if self.URLCONF_MODULES is not None:
                urlconf_modules.extend(self.URLCONF_MODULES)

        for urlconf in urlconf_modules:
            if urlconf in sys.modules:
                reload(sys.modules[urlconf])
        clear_url_caches()

        # Resolve a URL so that the new urlconf gets loaded
        resolve('/')

    def setUp(self):
        """Reset Django urls before tests and after tests

        If you need to reset `urls.py` from a particular Django app (or apps),
        specify these modules by setting the URLCONF_MODULES class attribute.

        Examples:

            # Reload only the root urls.py
            URLCONF_MODULES = None

            # Reload urls from my_app
            URLCONF_MODULES = ['myapp.url']

            # Reload urls from my_app and another_app
            URLCONF_MODULES = ['myapp.url', 'another_app.urls']

        """
        super(UrlResetMixin, self).setUp()

        self.reset_urls()
        self.addCleanup(self.reset_urls)


class EventTestMixin(object):
    """
    Generic mixin for verifying that events were emitted during a test.
    """
    def setUp(self, tracker):
        super(EventTestMixin, self).setUp()
        patcher = patch(tracker)
        self.mock_tracker = patcher.start()
        self.addCleanup(patcher.stop)

    def assert_no_events_were_emitted(self):
        """
        Ensures no events were emitted since the last event related assertion.
        """
        self.assertFalse(self.mock_tracker.emit.called)

    def assert_event_emitted(self, event_name, **kwargs):
        """
        Verify that an event was emitted with the given parameters.
        """
        self.mock_tracker.emit.assert_any_call(
            event_name,
            kwargs
        )

    def assert_event_emission_count(self, event_name, expected_count):
        """
        Verify that the event with the given name was emitted
        a specific number of times.
        """
        actual_count = 0
        for call_args in self.mock_tracker.emit.call_args_list:
            if call_args[0][0] == event_name:
                actual_count += 1
        self.assertEqual(actual_count, expected_count)

    def reset_tracker(self):
        """
        Reset the mock tracker in order to forget about old events.
        """
        self.mock_tracker.reset_mock()

    def get_latest_call_args(self):
        """
        Return the arguments of the latest call to emit.
        """
        return self.mock_tracker.emit.call_args[0]


class PatchMediaTypeMixin(object):
    """
    Generic mixin for verifying unsupported media type in PATCH
    """
    def test_patch_unsupported_media_type(self):
        response = self.client.patch(
            self.url,
            json.dumps({}),
            content_type=self.unsupported_media_type
        )
        self.assertEqual(response.status_code, 415)


def patch_testcase():
    """
    Disable commit_on_success decorators for tests in TestCase subclasses.

    Since tests in TestCase classes are wrapped in an atomic block, we
    cannot use transaction.commit() or transaction.rollback().
    https://docs.djangoproject.com/en/1.8/topics/testing/tools/#django.test.TransactionTestCase
    """

    def enter_atomics_wrapper(wrapped_func):
        """
        Wrapper for TestCase._enter_atomics
        """
        wrapped_func = wrapped_func.__func__

        def _wrapper(*args, **kwargs):
            """
            Method that performs atomic-entering accounting.
            """
            OuterAtomic.ALLOW_NESTED = True
            if not hasattr(OuterAtomic, 'atomic_for_testcase_calls'):
                OuterAtomic.atomic_for_testcase_calls = 0
            OuterAtomic.atomic_for_testcase_calls += 1
            return wrapped_func(*args, **kwargs)
        return classmethod(_wrapper)

    def rollback_atomics_wrapper(wrapped_func):
        """
        Wrapper for TestCase._rollback_atomics
        """
        wrapped_func = wrapped_func.__func__

        def _wrapper(*args, **kwargs):
            """
            Method that performs atomic-rollback accounting.
            """
            OuterAtomic.ALLOW_NESTED = False
            OuterAtomic.atomic_for_testcase_calls -= 1
            return wrapped_func(*args, **kwargs)
        return classmethod(_wrapper)

    # pylint: disable=protected-access
    TestCase._enter_atomics = enter_atomics_wrapper(TestCase._enter_atomics)
    TestCase._rollback_atomics = rollback_atomics_wrapper(TestCase._rollback_atomics)


def patch_sessions():
    """
    Override the Test Client's session and login to support safe cookies.
    """
    from openedx.core.djangoapps.safe_sessions.testing import safe_cookie_test_session_patch
    safe_cookie_test_session_patch()
