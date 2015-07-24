import sys

from mock import patch

from django.conf import settings
from django.core.urlresolvers import clear_url_caches, resolve

def reset_urls(feature_flag_overrides=None, urlconf_modules=None):
    """Reset `urls.py` for a set of Django apps."""
    feature_flag_overrides = feature_flag_overrides or {}

    with patch.dict("django.conf.settings.FEATURES", feature_flag_overrides):
        urlconf_modules = urlconf_modules or [settings.ROOT_URLCONF]
        for urlconf in urlconf_modules:
            if urlconf in sys.modules:
                reload(sys.modules[urlconf])

        clear_url_caches()

        # Resolve a URL so that the new urlconf gets loaded
        resolve('/')


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
