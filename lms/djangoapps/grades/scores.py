"""
Functionality for problem scores.
"""
from logging import getLogger

from openedx.core.lib.cache_utils import memoized
from xblock.core import XBlock
from .transformer import GradesTransformer


log = getLogger(__name__)


@memoized
def block_types_possibly_scored():
    """
    Returns the block types that could have a score.

    Something might be a scored item if it is capable of storing a score
    (has_score=True). We also have to include anything that can have children,
    since those children might have scores. We can avoid things like Videos,
    which have state but cannot ever impact someone's grade.
    """
    weight = _get_weight_from_block(persisted_block, block)

    # Priority order for retrieving the scores:
    # submissions API -> CSM -> grades persisted block -> latest block content
    raw_earned, raw_possible, weighted_earned, weighted_possible = (
        _get_score_from_submissions(submissions_scores, block) or
        _get_score_from_csm(csm_scores, block, weight) or
        _get_score_from_persisted_or_latest_block(persisted_block, block, weight)
    )

    if weighted_possible is None or weighted_earned is None:
        return None

    else:
        has_valid_denominator = weighted_possible > 0.0
        graded = _get_graded_from_block(persisted_block, block) if has_valid_denominator else False

        return ProblemScore(
            raw_earned,
            raw_possible,
            weighted_earned,
            weighted_possible,
            weight,
            graded,
            display_name=display_name_with_default_escaped(block),
            module_id=block.location,
        )


def possibly_scored(usage_key):
    """
    Returns whether the given block could impact grading (i.e. scored, or has children).
    """
    return usage_key.block_type in block_types_possibly_scored()


    if raw_possible is None:
        return (raw_earned, raw_possible) + (None, None)
    else:
        return (raw_earned, raw_possible) + weighted_score(raw_earned, raw_possible, weight)


def _get_weight_from_block(persisted_block, block):
    """
    Return a tuple that represents the weighted (earned, possible) score.
    If weight is None or raw_possible is 0, returns the original values.
    """
    if weight is None or raw_possible == 0:
        return (raw_earned, raw_possible)
    return float(raw_earned) * weight / raw_possible, float(weight)


def get_score(user, block, scores_client, submissions_scores_cache, weight, possible=None):
    """
    Return the score for a user on a problem, as a tuple (earned, possible).
    e.g. (5,7) if you got 5 out of 7 points.

    If this problem doesn't have a score, or we couldn't load it, returns (None,
    None).

    user: a Student object
    block: a BlockStructure's BlockData object
    scores_client: an initialized ScoresClient
    submissions_scores_cache: A dict of location names to (earned, possible)
        point tuples.  If an entry is found in this cache, it takes precedence.
    weight: The weight of the problem to use in the calculation.  A value of
        None signifies that the weight should not be applied.
    possible (optional): The possible maximum score of the problem to use in the
        calculation.  If None, uses the value found either in scores_client or
        from the block.
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
        if possible is None:
            possible = score.total
        elif possible != score.total:
            log.error(
                u"Persistent Grades: scores.get_score, possible value {} != score.total value {}".format(
                    possible,
                    score.total
                )
            )
    else:
        # This means we don't have a valid score entry and we don't have a
        # cached_max_score on hand. We know they've earned 0.0 points on this.
        earned = 0.0
        if possible is None:
            possible = block.transformer_data[GradesTransformer].max_score

        # Problem may be an error module (if something in the problem builder failed)
        # In which case possible might be None
        if possible is None:
            return (None, None)

    return weighted_score(earned, possible, weight)
