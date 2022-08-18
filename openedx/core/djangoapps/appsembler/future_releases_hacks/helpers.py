"""
Future release hacks
"""

from completion.exceptions import UnavailableCompletionData
from completion.models import BlockCompletion


def get_key_to_last_completed_block(user, context_key):
    """
    Helper to simulate completion.utilities.get_key_to_last_completed_block version 4. We need this version to fix
    a bug in dashboard Resume Course button, but we cannot upgrade the package within Juniper. RED-3276
    """
    last_completed_block = BlockCompletion.get_latest_block_completed(user, context_key)

    if last_completed_block is not None:
        return last_completed_block.full_block_key

    raise UnavailableCompletionData(context_key)
