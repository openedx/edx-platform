"""
Utility Mixins for unit tests
"""

import json
import sys

from mock import patch

from django.conf import settings
from django.core.urlresolvers import clear_url_caches, resolve
from django.test import TestCase

from util.db import OuterAtomic, CommitOnSuccessManager


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

    def _reset_urls(self, urlconf_modules):
        """Reset `urls.py` for a set of Django apps."""
        for urlconf in urlconf_modules:
            if urlconf in sys.modules:
                reload(sys.modules[urlconf])
        clear_url_caches()

        # Resolve a URL so that the new urlconf gets loaded
        resolve('/')

    def setUp(self, *args, **kwargs):
        """Reset Django urls before tests and after tests

        If you need to reset `urls.py` from a particular Django app (or apps),
        specify these modules in *args.

        Examples:

            # Reload only the root urls.py
            super(MyTestCase, self).setUp()

            # Reload urls from my_app
            super(MyTestCase, self).setUp("my_app.urls")

            # Reload urls from my_app and another_app
            super(MyTestCase, self).setUp("my_app.urls", "another_app.urls")

        """
        super(UrlResetMixin, self).setUp(**kwargs)

        urlconf_modules = [settings.ROOT_URLCONF]
        if args:
            urlconf_modules.extend(args)

        self._reset_urls(urlconf_modules)
        self.addCleanup(lambda: self._reset_urls(urlconf_modules))


class EventTestMixin(object):
    """
    Generic mixin for verifying that events were emitted during a test.
    """
    def setUp(self, tracker):
        super(EventTestMixin, self).setUp()
        self.tracker = tracker
        patcher = patch(self.tracker)
        self.mock_tracker = patcher.start()
        self.addCleanup(patcher.stop)

    def assert_no_events_were_emitted(self):
        """
        Ensures no events were emitted since the last event related assertion.
        """
        self.assertFalse(self.mock_tracker.emit.called)  # pylint: disable=maybe-no-member

    def assert_event_emitted(self, event_name, **kwargs):
        """
        Verify that an event was emitted with the given parameters.
        """
        self.mock_tracker.emit.assert_any_call(  # pylint: disable=maybe-no-member
            event_name,
            kwargs
        )

    def reset_tracker(self):
        """
        Reset the mock tracker in order to forget about old events.
        """
        self.mock_tracker.reset_mock()


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
            CommitOnSuccessManager.ENABLED = False
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
            CommitOnSuccessManager.ENABLED = True
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
