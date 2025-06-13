""" Utility functions related to django storages """

from typing import Optional, List
from django.conf import settings
from django.core.files.storage import storages
from django.utils.module_loading import import_string


def resolve_storage_backend(
        storage_key: str,
        legacy_setting_key: str,
        legacy_sec_setting_keys: List[str] = None,
        options: Optional[dict] = None):
    """
    Configures and returns a Django `Storage` instance, compatible with both Django 4 and Django 5.
    Params:
        storage_key = The key name saved in Django storages settings.
        legacy_setting_key = The key name saved in Django settings.
        legacy_sec_setting_keys = List of keys to get the storage class.
            For legacy dict settings like settings.BLOCK_STRUCTURES_SETTINGS.get('STORAGE_CLASS'),
            it is necessary to access a second-level key or above to retrieve the class path.
        legacy_options = Kwargs for the storage class.
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
    if isinstance(storage_path, dict) and legacy_sec_setting_keys:
        for deep_setting_key in legacy_sec_setting_keys:
            # For legacy dict settings like settings.CUSTOM_STORAGE = {"BACKEND": "cms.custom.."}
            storage_path = storage_path.get(deep_setting_key)
    storages_config = getattr(settings, 'STORAGES', {})

    if options is None:
        options = {}

    if storage_key in storages_config:
        # Use case 1: STORAGES is defined
        # If STORAGES is present, we retrieve it through the storages API
        # settings.py must define STORAGES like:
        # STORAGES = {
        #     "default": {"BACKEND": "...", "OPTIONS": {...}},
        #     "custom": {"BACKEND": "...", "OPTIONS": {...}},
        # }
        # See: https://docs.djangoproject.com/en/5.2/ref/settings/#std-setting-STORAGES
        return storages[storage_key]

    # Use case 2: Legacy settings
    # Fallback to import the storage_path (Obtained from django settings) manually
    StorageClass = import_string(storage_path or settings.DEFAULT_FILE_STORAGE)
    return StorageClass(**options)
