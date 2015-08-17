import sys

from mock import patch

from django.conf import settings
from django.core.urlresolvers import clear_url_caches, resolve


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
