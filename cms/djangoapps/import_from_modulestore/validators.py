"""
Validators for the import_from_modulestore app.
"""
from typing import Sequence

from opaque_keys.edx.keys import UsageKey

from .data import CompositionLevel


def validate_usage_keys_to_import(usage_keys: Sequence[str | UsageKey]):
    """
    Validate the usage keys to import.

    Currently, supports importing from the modulestore only by chapters.
    """
    for usage_key in usage_keys:
        if isinstance(usage_key, str):
            usage_key = UsageKey.from_string(usage_key)
        if usage_key.block_type != 'chapter':
            raise ValueError(f'Importing from modulestore only supports chapters, not {usage_key.block_type}')


def validate_composition_level(composition_level):
    if composition_level not in CompositionLevel.values():
        raise ValueError(f'Invalid composition level: {composition_level}')
