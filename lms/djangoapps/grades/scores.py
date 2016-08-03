"""
Functionality for problem scores.
"""
from openedx.core.lib.cache_utils import memoized
from xblock.core import XBlock
from .transformer import GradesTransformer


@memoized
def block_types_possibly_scored():
    """
    Returns the block types that could have a score.

    Something might be a scored item if it is capable of storing a score
    (has_score=True). We also have to include anything that can have children,
    since those children might have scores. We can avoid things like Videos,
    which have state but cannot ever impact someone's grade.
    """
    return frozenset(
        cat for (cat, xblock_class) in XBlock.load_classes() if (
            getattr(xblock_class, 'has_score', False) or getattr(xblock_class, 'has_children', False)
        )
    )


def possibly_scored(usage_key):
    """
    Returns whether the given block could impact grading (i.e. scored, or has children).
    """
    return usage_key.block_type in block_types_possibly_scored()


def weighted_score(raw_earned, raw_possible, weight):
    """Return a tuple that represents the weighted (correct, total) score."""
    # If there is no weighting, or weighting can't be applied, return input.
    if weight is None or raw_possible == 0:
        return (raw_earned, raw_possible)
    return float(raw_earned) * weight / raw_possible, float(weight)


def get_score(user, block, scores_client, submissions_scores_cache):
    """
    Return the score for a user on a problem, as a tuple (earned, possible).
    e.g. (5,7) if you got 5 out of 7 points.

    If this problem doesn't have a score, or we couldn't load it, returns (None,
    None).

    user: a Student object
    block: a BlockStructure's BlockData object
    scores_client: an initialized ScoresClient
    submissions_scores_cache: A dict of location names to (earned, possible) point tuples.
           If an entry is found in this cache, it takes precedence.
    """
    submissions_scores_cache = submissions_scores_cache or {}

    if not user.is_authenticated():
        return (None, None)

    location_url = unicode(block.location)
    if location_url in submissions_scores_cache:
        return submissions_scores_cache[location_url]

    if not getattr(block, 'has_score', False):
        # These are not problems, and do not have a score
        return (None, None)

    # Check the score that comes from the ScoresClient (out of CSM).
    # If an entry exists and has a total associated with it, we trust that
    # value. This is important for cases where a student might have seen an
    # older version of the problem -- they're still graded on what was possible
    # when they tried the problem, not what it's worth now.
    score = scores_client.get(block.location)
    if score and score.total is not None:
        # We have a valid score, just use it.
        earned = score.correct if score.correct is not None else 0.0
        possible = score.total
    else:
        # This means we don't have a valid score entry and we don't have a
        # cached_max_score on hand. We know they've earned 0.0 points on this.
        earned = 0.0
        possible = block.transformer_data[GradesTransformer].max_score

        # Problem may be an error module (if something in the problem builder failed)
        # In which case possible might be None
        if possible is None:
            return (None, None)

    return weighted_score(earned, possible, block.weight)
