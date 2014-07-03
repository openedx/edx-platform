from django.utils.unittest import skip
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from opaque_keys.edx.locator import CourseLocator
from xmodule.modulestore import ModuleStoreEnum
from contentstore.tests.utils import CourseTestCase


@skip("Pending integration with latest opaque-keys library - need removal of offering, make_asset_key on CourseLocator, etc.")
class CloneCourseTest(CourseTestCase):
    def test_clone_course(self):
        # 1. import and populate test toy course
        mongo_course1_id = self.import_and_populate_course()
        self.check_populated_course(mongo_course1_id)

        # 2. clone course (mongo -> mongo)
        # TODO - This is currently failing since clone_course doesn't handle Private content - fails on Publish
        mongo_course2_id = SlashSeparatedCourseKey('edX2', 'toy2', '2013_Fall')
        self.store.clone_course(mongo_course1_id, mongo_course2_id, self.user.id)
        self.assertCoursesEqual(mongo_course1_id, mongo_course2_id)

        # 3. clone course (mongo -> split)
        with self.store.set_default_store(ModuleStoreEnum.Type.split):
            split_course3_id = CourseLocator(org="edx3", offering="split3", branch=ModuleStoreEnum.BranchName.draft)
            self.store.clone_course(mongo_course2_id, split_course3_id, self.user.id)
            self.assertCoursesEqual(mongo_course2_id, split_course3_id)

            # 4. clone course (split -> split)
            split_course4_id = CourseLocator(org="edx4", offering="split4", branch=ModuleStoreEnum.BranchName.draft)
            self.store.clone_course(split_course3_id, split_course4_id, self.user.id)
            self.assertCoursesEqual(split_course3_id, split_course4_id)
