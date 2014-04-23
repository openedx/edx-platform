from django.conf import settings
from django.test.utils import override_settings
from lms.lib.xblock.runtime import LmsMetadataService
from xmodule.modulestore.tests.django_utils import draft_mongo_store_config, ModuleStoreTestCase

TEST_MODULESTORE = draft_mongo_store_config(settings.TEST_ROOT / "data")

@override_settings(MODULESTORE=TEST_MODULESTORE)
class TestPreviewLmsMetadataService(ModuleStoreTestCase):

    def test_preview_enabled(self):
        service = LmsMetadataService()
        self.assertTrue(service.is_preview_enabled())


class TestProdLmsMetadataService(ModuleStoreTestCase):

    def test_preview_not_enabled(self):
        service = LmsMetadataService()
        self.assertFalse(service.is_preview_enabled())