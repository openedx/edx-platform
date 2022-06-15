"""
Helper method to indicate when the blockstore app API is enabled.
"""
from django.conf import settings
from .waffle import BLOCKSTORE_USE_BLOCKSTORE_APP_API  # pylint: disable=invalid-django-waffle-import


def use_blockstore_app():
    """
    Use the Blockstore app API if the settings say to (e.g. in test)
    or if the waffle switch is enabled.
    """
    return settings.BLOCKSTORE_USE_BLOCKSTORE_APP_API or BLOCKSTORE_USE_BLOCKSTORE_APP_API.is_enabled()
