"""
Validators for the import_from_modulestore app.
"""
from django.utils.translation import gettext_lazy as _

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey

from .data import CompositionLevel


def validate_usage_keys_to_import(usage_keys: list[str | UsageKey]):
    """
    Validate the usage keys to import.

    Currently, supports importing from the modulestore only by chapters.
    """
    for usage_key in usage_keys:
        if isinstance(usage_key, str):
            try:
                usage_key = UsageKey.from_string(usage_key)
            except InvalidKeyError:
                raise ValueError(_(f'Invalid usage key: {usage_key}'))
        if usage_key.block_type != 'chapter':
            raise InvalidKeyError(_(f'Importing from modulestore only supports chapters, not {usage_key.block_type}'))

def validate_composition_level(composition_level):
    if composition_level not in CompositionLevel.values():
        raise ValueError(
            _('Invalid composition level: {composition_level}').format(composition_level=composition_level)
        )
