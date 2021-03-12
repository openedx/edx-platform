"""
Helpers functions for grades and scores.
"""
import math


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


def round_away_from_zero(number, digits=0):
    """
    Round numbers using the 'away from zero' strategy as opposed to the
    'Banker's rounding strategy.'  The strategy refers to how we round when
    a number is half way between two numbers.  eg. 0.5, 1.5, etc. In python 2
    positive numbers in this category would be rounded up and negative numbers
    would be rounded down. ie. away from zero.  In python 3 numbers round
    towards even.  So 0.5 would round to 0 but 1.5 would round to 2.

    See here for more on floating point rounding strategies:
    https://en.wikipedia.org/wiki/IEEE_754#Rounding_rules

    We want to continue to round away from zero so that student grades remain
    consistent and don't suddenly change.
    """
    p = 10.0 ** digits

    if number >= 0:
        return float(math.floor((number * p) + 0.5)) / p
    else:
        return float(math.ceil((number * p) - 0.5)) / p
