"""
All business logic related to fetching generic Learning Sequences information.
By 'generic', we mean context-agnostic; the data returned by these functions
should not be specific to Courses, Libraries, Pathways, or any other context
in which Learning Sequences can exist.

Do not import from this module directly.
Use openedx.core.djangoapps.content.learning_sequences.api -- that
__init__.py imports from here, and is a more stable place to import from.
"""
from opaque_keys.edx.keys import UsageKey

from ..data import LearningSequenceData
from ..models import LearningSequence


def get_learning_sequence(sequence_key: UsageKey) -> LearningSequenceData:
    """
    Load generic data for a learning sequence given its usage key.
    """
    try:
        sequence = LearningSequence.objects.get(usage_key=sequence_key)
    except LearningSequence.DoesNotExist as exc:
        raise LearningSequenceData.DoesNotExist(
            f"no such sequence with usage_key='{sequence_key}'"
        ) from exc
    return _make_sequence_data(sequence)


def get_learning_sequence_by_hash(sequence_key_hash: str) -> LearningSequenceData:
    """
    Load generic data for a learning sequence given the hash of its usage key.

    WARNING! This is an experimental API function!
    We do not currently handle the case of usage key hash collisions.

    Before considering this API method stable, will either need to:
    1. confirm that the probability of usage key hash collision (accounting for
       potentially multiple orders of magnitude of catalog growth) is acceptably
       small, or
    2. declare that hash keys are only unique within a given learning context,
       and update this API function to require a `learning_context_key` argument.
    See TNL-8638.
    """
    sequences = LearningSequence.objects.filter(usage_key_hash=sequence_key_hash)
    if not sequences:
        raise LearningSequenceData.DoesNotExist(
            f"no such sequence with usage_key_hash={sequence_key_hash!r}"
        )
    if len(sequences) > 1:
        usage_keys_list = ', '.join([
            str(sequence.usage_key) for sequence in sequences
        ])
        raise Exception(
            f"Two or more sequences' usage keys hash to {sequence_key_hash!r}! "
            f"Colliding usage keys: [{usage_keys_list}]."
        )
    return _make_sequence_data(sequences[0])


def _make_sequence_data(sequence: LearningSequence) -> LearningSequenceData:
    """
    Build a LearningSequenceData instance from a LearningSequence model instance.
    """
    return LearningSequenceData(
        usage_key=sequence.usage_key,
        usage_key_hash=sequence.usage_key_hash,
        title=sequence.title,
    )
