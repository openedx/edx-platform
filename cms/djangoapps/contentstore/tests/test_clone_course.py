"""
Unit tests for cloning a course between the same and different module stores.
"""


import json

import six
from django.conf import settings
from mock import Mock, patch
from opaque_keys.edx.locator import CourseLocator

from cms.djangoapps.contentstore.tasks import rerun_course
from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from common.djangoapps.course_action_state.managers import CourseRerunUIStateManager
from common.djangoapps.course_action_state.models import CourseRerunState
from common.djangoapps.student.auth import has_course_author_access
from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.django import contentstore
from xmodule.modulestore import EdxJSONEncoder, ModuleStoreEnum
from xmodule.modulestore.tests.factories import CourseFactory

TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT


class CloneCourseTest(CourseTestCase):
    """
    Unit tests for cloning a course
    """
    def test_clone_course(self):
        """Tests cloning of a course as follows: XML -> Mongo (+ data) -> Mongo -> Split -> Split"""
        # 1. import and populate test toy course
        mongo_course1_id = self.import_and_populate_course()
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

    def test_space_in_asset_name_for_rerun_course(self):
        """
        Tests check the scenario where one course which has an asset with percentage(%) in its
        name, it should re-run successfully.
        """
        org = 'edX'
        course_number = 'CS101'
        course_run = '2015_Q1'
        display_name = 'rerun'
        fields = {'display_name': display_name}
        course_assets = set([u'subs_Introduction%20To%20New.srt.sjson'], )

        # Create a course using split modulestore
        course = CourseFactory.create(
            org=org,
            number=course_number,
            run=course_run,
            display_name=display_name,
            default_store=ModuleStoreEnum.Type.split
        )

        # add an asset
        asset_key = course.id.make_asset_key('asset', 'subs_Introduction%20To%20New.srt.sjson')
        content = StaticContent(
            asset_key, 'Dummy assert', 'application/json', 'dummy data',
        )
        contentstore().save(content)

        # Get & verify all assets of the course
        assets, count = contentstore().get_all_content_for_course(course.id)
        self.assertEqual(count, 1)
        self.assertEqual(set([asset['asset_key'].block_id for asset in assets]), course_assets)

        # rerun from split into split
        split_rerun_id = CourseLocator(org=org, course=course_number, run="2012_Q2")
        CourseRerunState.objects.initiated(course.id, split_rerun_id, self.user, fields['display_name'])
        result = rerun_course.delay(
            six.text_type(course.id),
            six.text_type(split_rerun_id),
            self.user.id,
            json.dumps(fields, cls=EdxJSONEncoder)
        )

        # Check if re-run was successful
        self.assertEqual(result.get(), "succeeded")
        rerun_state = CourseRerunState.objects.find_first(course_key=split_rerun_id)
        self.assertEqual(rerun_state.state, CourseRerunUIStateManager.State.SUCCEEDED)

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
        result = rerun_course.delay(six.text_type(mongo_course1_id), six.text_type(split_course3_id), self.user.id,
                                    json.dumps(fields, cls=EdxJSONEncoder))
        self.assertEqual(result.get(), "succeeded")
        self.assertTrue(has_course_author_access(self.user, split_course3_id), "Didn't grant access")
        rerun_state = CourseRerunState.objects.find_first(course_key=split_course3_id)
        self.assertEqual(rerun_state.state, CourseRerunUIStateManager.State.SUCCEEDED)

        # try creating rerunning again to same name and ensure it generates error
        result = rerun_course.delay(six.text_type(mongo_course1_id), six.text_type(split_course3_id), self.user.id)
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
            result = rerun_course.delay(six.text_type(split_course3_id), six.text_type(split_course4_id), self.user.id,
                                        json.dumps(fields, cls=EdxJSONEncoder))
            self.assertIn("exception: ", result.get())
            self.assertIsNone(self.store.get_course(split_course4_id), "Didn't delete course after error")
            CourseRerunState.objects.find_first(
                course_key=split_course4_id,
                state=CourseRerunUIStateManager.State.FAILED
            )
