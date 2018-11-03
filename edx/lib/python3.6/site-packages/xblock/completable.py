"""
This module defines CompletableXBlockMixin and completion mode enumeration.
"""
from __future__ import absolute_import, unicode_literals


class XBlockCompletionMode(object):
    """
    Enumeration for completion modes.
    """
    COMPLETABLE = "completable"
    AGGREGATOR = "aggregator"
    EXCLUDED = "excluded"

    @classmethod
    def get_mode(cls, block_class):
        """
        Return the effective completion mode for a given block.

        Defaults to XBlockCompletionMode.COMPLETABLE.
        """
        return getattr(block_class, 'completion_mode', cls.COMPLETABLE)


class CompletableXBlockMixin(object):
    """
    This mixin sets attributes and provides helper method to integrate XBlock with Completion API.
    """

    has_custom_completion = True
    completion_mode = XBlockCompletionMode.COMPLETABLE

    # To read more on the debate about using the terms percent vs ratio, see:
    # https://openedx.atlassian.net/wiki/spaces/OpenDev/pages/245465398/Naming+with+Percent+or+Ratio
    def emit_completion(self, completion_percent):
        """
        Emits completion event through Completion API.

        Unlike grading API, calling this method allows completion to go down - i.e. emitting a value of 0.0 on
        a previously completed block indicates that it is no longer considered complete.

        Arguments:
            completion_percent (float): Completion in range [0.0; 1.0] (inclusive), where 0.0 means the block
            is not completed, 1.0 means the block is fully completed.

        Returns:
            None
        """
        completion_mode = XBlockCompletionMode.get_mode(self)
        if not self.has_custom_completion or completion_mode != XBlockCompletionMode.COMPLETABLE:
            raise AttributeError(
                "Using `emit_completion` requires `has_custom_completion == True` (was {}) "
                "and `completion_mode == 'completable'` (was {})".format(
                    self.has_custom_completion, completion_mode,
                )
            )

        if completion_percent is None or not 0.0 <= completion_percent <= 1.0:
            raise ValueError("Completion percent must be in [0.0; 1.0] interval, {} given".format(completion_percent))

        self.runtime.publish(
            self,
            'completion',
            {'completion': completion_percent},
        )
