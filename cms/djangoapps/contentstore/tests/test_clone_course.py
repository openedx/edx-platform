"""
Unit tests for cloning a course between the same and different module stores.
"""
import json
from opaque_keys.edx.locator import CourseLocator
from xmodule.modulestore import ModuleStoreEnum, EdxJSONEncoder
from contentstore.tests.utils import CourseTestCase
from contentstore.tasks import rerun_course
from contentstore.views.access import has_course_access
from course_action_state.models import CourseRerunState
from course_action_state.managers import CourseRerunUIStateManager
from mock import patch, Mock


class CloneCourseTest(CourseTestCase):
    """
    Unit tests for cloning a course
    """
    def test_clone_course(self):
        """Tests cloning of a course as follows: XML -> Mongo (+ data) -> Mongo -> Split -> Split"""
        # 1. import and populate test toy course
        mongo_course1_id = self.import_and_populate_course()

        # 2. clone course (mongo -> mongo)
        # TODO - This is currently failing since clone_course doesn't handle Private content - fails on Publish
        # mongo_course2_id = SlashSeparatedCourseKey('edX2', 'toy2', '2013_Fall')
        # self.store.clone_course(mongo_course1_id, mongo_course2_id, self.user.id)
        # self.assertCoursesEqual(mongo_course1_id, mongo_course2_id)
        # self.check_populated_course(mongo_course2_id)

        # NOTE: When the code above is uncommented this can be removed.
        mongo_course2_id = mongo_course1_id

        # 3. clone course (mongo -> split)
        with self.store.default_store(ModuleStoreEnum.Type.split):
            split_course3_id = CourseLocator(
                org="edx3", course="split3", run="2013_Fall"
            )
            self.store.clone_course(mongo_course2_id, split_course3_id, self.user.id)
            self.assertCoursesEqual(mongo_course2_id, split_course3_id)

            # 4. clone course (split -> split)
            split_course4_id = CourseLocator(
                org="edx4", course="split4", run="2013_Fall"
            )
            self.store.clone_course(split_course3_id, split_course4_id, self.user.id)
            self.assertCoursesEqual(split_course3_id, split_course4_id)

    def test_rerun_course(self):
        """
        Unit tests for :meth: `contentstore.tasks.rerun_course`
        """
        mongo_course1_id = self.import_and_populate_course()

        # rerun from mongo into split
        split_course3_id = CourseLocator(
            org="edx3", course="split3", run="rerun_test"
        )
        # Mark the action as initiated
        fields = {'display_name': 'rerun'}
        CourseRerunState.objects.initiated(mongo_course1_id, split_course3_id, self.user, fields['display_name'])
        result = rerun_course.delay(unicode(mongo_course1_id), unicode(split_course3_id), self.user.id,
                                    json.dumps(fields, cls=EdxJSONEncoder))
        self.assertEqual(result.get(), "succeeded")
        self.assertTrue(has_course_access(self.user, split_course3_id), "Didn't grant access")
        rerun_state = CourseRerunState.objects.find_first(course_key=split_course3_id)
        self.assertEqual(rerun_state.state, CourseRerunUIStateManager.State.SUCCEEDED)

        # try creating rerunning again to same name and ensure it generates error
        result = rerun_course.delay(unicode(mongo_course1_id), unicode(split_course3_id), self.user.id)
        self.assertEqual(result.get(), "duplicate course")
        # the below will raise an exception if the record doesn't exist
        CourseRerunState.objects.find_first(
            course_key=split_course3_id,
            state=CourseRerunUIStateManager.State.FAILED
        )

        # try to hit the generic exception catch
        with patch('xmodule.modulestore.split_mongo.mongo_connection.MongoConnection.insert_course_index', Mock(side_effect=Exception)):
            split_course4_id = CourseLocator(org="edx3", course="split3", run="rerun_fail")
            fields = {'display_name': 'total failure'}
            CourseRerunState.objects.initiated(split_course3_id, split_course4_id, self.user, fields['display_name'])
            result = rerun_course.delay(unicode(split_course3_id), unicode(split_course4_id), self.user.id,
                                        json.dumps(fields, cls=EdxJSONEncoder))
            self.assertIn("exception: ", result.get())
            self.assertIsNone(self.store.get_course(split_course4_id), "Didn't delete course after error")
            CourseRerunState.objects.find_first(
                course_key=split_course4_id,
                state=CourseRerunUIStateManager.State.FAILED
            )
