"""
Tests of modulestore semantics: How do the interfaces methods of ModuleStore relate to each other?
"""

from xmodule.modulestore.tests.utils import (
    PureModulestoreTestCase, MongoModulestoreBuilder,
    SPLIT_MODULESTORE_SETUP
)
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.factories import CourseFactory

class AboutItemSemantics(PureModulestoreTestCase):
    """
    Verify the behavior of About items (which are intentionally orphaned, DIRECT_ONLY/autopublished)
    blocks intended to store snippets of course content.
    """

    __test__ = False

    def setUp(self):
        super(AboutItemSemantics, self).setUp()
        self.course = CourseFactory.create(
            org='test_org',
            number='999',
            run='test_run',
            display_name='My Test Course',
            modulestore=self.store
        )

        self.about_usage_key = self.course.id.make_usage_key('about', 'video')

    def assertAboutDoesntExist(self):
        with self.assertRaises(ItemNotFoundError):
            self.store.get_item(self.about_usage_key, revision=ModuleStoreEnum.RevisionOption.published_only)
        with self.assertRaises(ItemNotFoundError):
            self.store.get_item(self.about_usage_key, revision=ModuleStoreEnum.RevisionOption.draft_only)

        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):
            with self.assertRaises(ItemNotFoundError):
                self.store.get_item(self.about_usage_key)

        with self.store.branch_setting(ModuleStoreEnum.Branch.published_only):
            with self.assertRaises(ItemNotFoundError):
                self.store.get_item(self.about_usage_key)

    def assertAboutHasContent(self, content):
        self.assertEquals(
            content,
            self.store.get_item(
                self.about_usage_key,
                revision=ModuleStoreEnum.RevisionOption.published_only
            ).data
        )
        self.assertEquals(
            content,
            self.store.get_item(
                self.about_usage_key,
                revision=ModuleStoreEnum.RevisionOption.draft_only
            ).data
        )

        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):
            self.assertEquals(
                content,
                self.store.get_item(
                    self.about_usage_key,
                ).data
            )

        with self.store.branch_setting(ModuleStoreEnum.Branch.published_only):
            self.assertEquals(
                content,
                self.store.get_item(
                    self.about_usage_key,
                ).data
            )

    def test_create(self):
        self.assertAboutDoesntExist()

        data_string = '<div>test data</div>'

        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):
            about_item = self.store.create_xblock(
                self.course.runtime,
                self.course.id,
                self.about_usage_key.block_type,
                block_id=self.about_usage_key.block_id
            )

            about_item.data = data_string
            self.store.update_item(about_item, ModuleStoreEnum.UserID.test, allow_not_found=True)

        self.assertAboutHasContent(data_string)

    def test_update(self):
        self.test_create()

        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):
            about_item = self.store.get_item(self.about_usage_key)

            data_string = "<div>different test data</div>"
            self.assertNotEquals(data_string, about_item.data)

            about_item.data = data_string

            self.store.update_item(about_item, ModuleStoreEnum.UserID.test, allow_not_found=True)

        self.assertAboutHasContent(data_string)

    def test_delete(self):
        self.test_create()

        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):
            self.store.delete_item(self.about_usage_key, ModuleStoreEnum.UserID.test)

        self.assertAboutDoesntExist()

class TestSplitAboutItemSemantics(AboutItemSemantics):
    MODULESTORE = SPLIT_MODULESTORE_SETUP
    __test__ = True


class TestMongoAboutItemSemantics(AboutItemSemantics):
    MODULESTORE = MongoModulestoreBuilder()
    __test__ = True
