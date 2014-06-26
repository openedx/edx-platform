"""
Unit tests for cloning a course between the same and different module stores.
"""
from django.utils.unittest.case import skipIf
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from opaque_keys.edx.locator import CourseLocator
from xmodule.modulestore import ModuleStoreEnum
from contentstore.tests.utils import CourseTestCase


@skipIf(
    not 'run' in CourseLocator.KEY_FIELDS,
    "Pending integration with latest opaque-keys library - need removal of offering, make_asset_key on CourseLocator, etc."
)
class CloneCourseTest(CourseTestCase):
    """
    Unit tests for cloning a course
    """
    def test_clone_course(self):
        """Tests cloning of a course as follows: XML -> Mongo (+ data) -> Mongo -> Split -> Split"""
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
            split_course3_id = CourseLocator(
                org="edx3", course="split3", run="2013_Fall", branch=ModuleStoreEnum.BranchName.draft
            )
            self.store.clone_course(mongo_course2_id, split_course3_id, self.user.id)
            self.assertCoursesEqual(mongo_course2_id, split_course3_id)

            # 4. clone course (split -> split)
            split_course4_id = CourseLocator(
                org="edx4", course="split4", run="2013_Fall", branch=ModuleStoreEnum.BranchName.draft
            )
            self.store.clone_course(split_course3_id, split_course4_id, self.user.id)
            self.assertCoursesEqual(split_course3_id, split_course4_id)
