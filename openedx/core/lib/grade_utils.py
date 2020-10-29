"""
Helpers functions for grades and scores.
"""


def compare_scores(earned1, possible1, earned2, possible2, treat_undefined_as_zero=False):
    """
    Returns a tuple of:
        1. Whether the 2nd set of scores is higher than the first.
        2. Grade percentage of 1st set of scores.
        3. Grade percentage of 2nd set of scores.
    If ``treat_undefined_as_zero`` is True, this function will treat
    cases where ``possible1`` or ``possible2`` is 0 as if
    the (earned / possible) score is 0.  If this flag is false,
    a ZeroDivisionError is raised.
    """
    try:
        percentage1 = float(earned1) / float(possible1)
    except ZeroDivisionError:
        if not treat_undefined_as_zero:
            raise
        percentage1 = 0.0

    try:
        percentage2 = float(earned2) / float(possible2)
    except ZeroDivisionError:
        if not treat_undefined_as_zero:
            raise
        percentage2 = 0.0

    is_higher = percentage2 >= percentage1
    return is_higher, percentage1, percentage2


def is_score_higher_or_equal(earned1, possible1, earned2, possible2, treat_undefined_as_zero=False):
    """
    Returns whether the 2nd set of scores is higher than the first.
    If ``treat_undefined_as_zero`` is True, this function will treat
    cases where ``possible1`` or ``possible2`` is 0 as if
    the (earned / possible) score is 0.  If this flag is false,
    a ZeroDivisionError is raised.
    """
    is_higher_or_equal, _, _ = compare_scores(earned1, possible1, earned2, possible2, treat_undefined_as_zero)
    return is_higher_or_equal
