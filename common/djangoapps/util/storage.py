""" Utility functions related to django storages """

import django
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils.module_loading import import_string


def resolve_storage_backend(storage_key, options=None):
    """
    Configures and returns a Django `Storage` instance, compatible with both Django 4 and Django 5.

    Main goal:
        Deprecate the use of `django.core.files.storage.get_storage_class`.
    How:
        Replace `get_storage_class` with direct configuration logic,
        ensuring backward compatibility with both Django 4 and Django 5 storage settings.
    Returns:
        An instance of the configured storage backend.
    Raises:
        ImportError: If the specified storage class cannot be imported.
    """

    storage_path = getattr(settings, storage_key, None)
    storages_config = getattr(settings, 'STORAGES', {})

    if options is None:
        options = {}

    if storage_key == "default":
        # Use case 1: Default storage
        # Works consistently across Django 4.2 and 5.x
        # In Django 4.2, default_storage uses DEFAULT_FILE_STORAGE
        # In Django 5.x, it uses STORAGES['default']
        return default_storage

    if django.VERSION >= (5, 0) and storage_key in storages_config:
        # Use case 2: Django 5+ with STORAGES defined
        # settings.py must define STORAGES like:
        # STORAGES = {
        #     "default": {"BACKEND": "...", "OPTIONS": {...}},
        #     "custom": {"BACKEND": "...", "OPTIONS": {...}},
        # }
        # See: https://docs.djangoproject.com/en/5.2/ref/settings/#std-setting-STORAGES
        from django.core.files.storage import storages
        return storages[storage_key]

    if not storage_path and storage_key in storages_config:
        # Use case 3: Transitional setup
        # Running on Django 4.x but using Django 5-style STORAGES config
        # Manually load the backend and options
        storage_path = storages_config.get(storage_key, {}).get("BACKEND")
        options = storages_config.get(storage_key, {}).get("OPTIONS", {})

    if not storage_path:
        # if no specific storage was resolved, use the default storage
        return default_storage

    # Fallback to import the storage_path manually
    StorageClass = import_string(storage_path)
    return StorageClass(**options)
