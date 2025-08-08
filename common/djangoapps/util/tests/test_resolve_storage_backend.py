"""
Tests for the resolve_storage_backend function in common.djangoapps.util.storage.
"""

from django.test import TestCase
from django.test.utils import override_settings

from common.djangoapps.util.storage import resolve_storage_backend


DEFAULT_STORAGE_CLASS_NAME = "FileSystemStorage"


class ResolveStorageTest(TestCase):
    """
    Tests for the resolve_storage_backend function.
    """

    @override_settings(
        BLOCK_STRUCTURES_SETTINGS="cms.djangoapps.contentstore.storage.ImportExportS3Storage"
    )
    def test_legacy_settings(self):
        storage = resolve_storage_backend(
            storage_key="block_structures_settings",
            legacy_setting_key="BLOCK_STRUCTURES_SETTINGS",
            options={}
        )
        assert storage.__class__.__name__ == "ImportExportS3Storage"

    @override_settings(
        BLOCK_STRUCTURES_SETTINGS={
            "STORAGE_CLASS": "cms.djangoapps.contentstore.storage.ImportExportS3Storage"
        }
    )
    def test_nested_legacy_settings(self):
        storage = resolve_storage_backend(
            storage_key="block_structures_settings",
            legacy_setting_key="BLOCK_STRUCTURES_SETTINGS",
            legacy_sec_setting_keys=["STORAGE_CLASS"],
            options={}
        )
        assert storage.__class__.__name__ == "ImportExportS3Storage"

    @override_settings(
        BLOCK_STRUCTURES_SETTINGS={
            "OTHER_KEY": "cms.djangoapps.contentstore.storage.ImportExportS3Storage"
        }
    )
    def test_nested_legacy_settings_failed(self):
        storage = resolve_storage_backend(
            storage_key="block_structures_settings",
            legacy_setting_key="BLOCK_STRUCTURES_SETTINGS",
            legacy_sec_setting_keys=["STORAGE_CLASS"],
            options={}
        )
        assert storage.__class__.__name__ == DEFAULT_STORAGE_CLASS_NAME
