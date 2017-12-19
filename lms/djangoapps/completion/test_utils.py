"""
Common functionality to support writing tests around completion.
"""

from . import waffle


class CompletionWaffleTestMixin(object):
    """
    Common functionality for completion waffle tests.
    """
    def override_waffle_switch(self, override):
        """
        Override the setting of the ENABLE_COMPLETION_TRACKING waffle switch
        for the course of the test.

        Parameters:
            override (bool): True if tracking should be enabled.
        """
        _waffle_overrider = waffle.waffle().override(waffle.ENABLE_COMPLETION_TRACKING, override)
        _waffle_overrider.__enter__()
        self.addCleanup(_waffle_overrider.__exit__, None, None, None)
