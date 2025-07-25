""" Utility functions related to django storages """

from typing import Optional
from django.conf import settings
from django.core.files.storage import default_storage, storages
from django.utils.module_loading import import_string


def resolve_storage_backend(storage_key: str, legacy_setting_key: str, options: Optional[dict] = None):
    """
    Configures and returns a Django `Storage` instance, compatible with both Django 4 and Django 5.
    Params:
        storage_key = The key name saved in Django storages settings.
        legacy_setting_key = The key name saved in Django settings.
        options = Kwargs for the storage class.
    Returns:
        An instance of the configured storage backend.
    Raises:
        ImportError: If the specified storage class cannot be imported.

    Main goal:
        Deprecate the use of `django.core.files.storage.get_storage_class`.

    How:
        Replace `get_storage_class` with direct configuration logic,
        ensuring backward compatibility with both Django 4 and Django 5 storage settings.
    """

    storage_path = getattr(settings, legacy_setting_key, None)
    storages_config = getattr(settings, 'STORAGES', {})

    if options is None:
        options = {}

    if storage_key == "default":
        # Use case 1: Default storage
        # Works consistently across Django 4.2 and 5.x.
        # In Django 4.2 and above, `default_storage` uses
        # either `DEFAULT_FILE_STORAGE` or `STORAGES['default']`.
        return default_storage

    if storage_key in storages_config:
        # Use case 2: STORAGES is defined
        # If STORAGES is present, we retrieve it through the storages API
        # settings.py must define STORAGES like:
        # STORAGES = {
        #     "default": {"BACKEND": "...", "OPTIONS": {...}},
        #     "custom": {"BACKEND": "...", "OPTIONS": {...}},
        # }
        # See: https://docs.djangoproject.com/en/5.2/ref/settings/#std-setting-STORAGES
        return storages[storage_key]

    if not storage_path:
        # Use case 3: No storage settings defined
        # If no storage settings are defined anywhere, use the default storage
        return default_storage

    # Use case 4: Legacy settings
    # Fallback to import the storage_path (Obtained from django settings) manually
    StorageClass = import_string(storage_path)
    return StorageClass(**options)
