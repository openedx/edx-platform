"""
Helpers functions for grades and scores.
"""


def compare_scores(earned1, possible1, earned2, possible2):
    """
    Returns a tuple of:
        1. Whether the 2nd set of scores is higher than the first.
        2. Grade percentage of 1st set of scores.
        3. Grade percentage of 2nd set of scores.
    """
    percentage1 = float(earned1) / float(possible1)
    percentage2 = float(earned2) / float(possible2)
    is_higher = percentage2 > percentage1
    return is_higher, percentage1, percentage2


def is_score_higher(earned1, possible1, earned2, possible2):
    """
    Returns whether the 2nd set of scores is higher than the first.
    """
    is_higher, _, _ = compare_scores(earned1, possible1, earned2, possible2)
    return is_higher
