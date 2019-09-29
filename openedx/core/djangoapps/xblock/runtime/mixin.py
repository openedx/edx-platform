"""
A mixin that provides functionality and default attributes for all XBlocks in
the new XBlock runtime.
"""


class LmsBlockMixin(object):
    """
    A mixin that provides functionality and default attributes for all XBlocks
    in the new XBlock runtime.

    These are not standard XBlock attributes but are used by the LMS (and
    possibly Studio).
    """

    # This indicates whether the XBlock has a score (e.g. it's a problem, not
    # static content). If it does, it should set this and provide scoring
    # functionality by inheriting xblock.scorable.ScorableXBlockMixin
    has_score = False
