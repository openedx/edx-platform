"""
Tests for CourseDetails
"""

import datetime
import ddt
from django.utils.timezone import UTC
from nose.plugins.attrib import attr

from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from openedx.core.djangoapps.self_paced.models import SelfPacedConfiguration
from openedx.core.djangoapps.models.course_details import CourseDetails, ABOUT_ATTRIBUTES


@attr(shard=2)
@ddt.ddt
class CourseDetailsTestCase(ModuleStoreTestCase):
    """
    Tests the first course settings page (course dates, overview, etc.).
    """
    def setUp(self):
        super(CourseDetailsTestCase, self).setUp()
        self.course = CourseFactory.create()

    def test_virgin_fetch(self):
        details = CourseDetails.fetch(self.course.id)
        self.assertEqual(details.org, self.course.location.org, "Org not copied into")
        self.assertEqual(details.course_id, self.course.location.course, "Course_id not copied into")
        self.assertEqual(details.run, self.course.location.name, "Course name not copied into")
        self.assertEqual(details.course_image_name, self.course.course_image)
        self.assertIsNotNone(details.start_date.tzinfo)
        self.assertIsNone(details.end_date, "end date somehow initialized " + str(details.end_date))
        self.assertIsNone(
            details.enrollment_start, "enrollment_start date somehow initialized " + str(details.enrollment_start)
        )
        self.assertIsNone(
            details.enrollment_end, "enrollment_end date somehow initialized " + str(details.enrollment_end)
        )
        self.assertIsNone(details.syllabus, "syllabus somehow initialized" + str(details.syllabus))
        self.assertIsNone(details.intro_video, "intro_video somehow initialized" + str(details.intro_video))
        self.assertIsNone(details.effort, "effort somehow initialized" + str(details.effort))
        self.assertIsNone(details.language, "language somehow initialized" + str(details.language))
        self.assertFalse(details.self_paced)

    def test_update_and_fetch(self):
        SelfPacedConfiguration(enabled=True).save()
        jsondetails = CourseDetails.fetch(self.course.id)
        jsondetails.syllabus = "<a href='foo'>bar</a>"
        # encode - decode to convert date fields and other data which changes form
        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, self.course.id):
            self.assertEqual(
                CourseDetails.update_from_json(self.course.id, jsondetails.__dict__, self.user).syllabus,
                jsondetails.syllabus, "After set syllabus"
            )
            jsondetails.short_description = "Short Description"
            self.assertEqual(
                CourseDetails.update_from_json(self.course.id, jsondetails.__dict__, self.user).short_description,
                jsondetails.short_description, "After set short_description"
            )
            jsondetails.overview = "Overview"
            self.assertEqual(
                CourseDetails.update_from_json(self.course.id, jsondetails.__dict__, self.user).overview,
                jsondetails.overview, "After set overview"
            )
            jsondetails.intro_video = "intro_video"
            self.assertEqual(
                CourseDetails.update_from_json(self.course.id, jsondetails.__dict__, self.user).intro_video,
                jsondetails.intro_video, "After set intro_video"
            )
            jsondetails.effort = "effort"
            self.assertEqual(
                CourseDetails.update_from_json(self.course.id, jsondetails.__dict__, self.user).effort,
                jsondetails.effort, "After set effort"
            )
            jsondetails.self_paced = True
            self.assertEqual(
                CourseDetails.update_from_json(self.course.id, jsondetails.__dict__, self.user).self_paced,
                jsondetails.self_paced
            )
            jsondetails.start_date = datetime.datetime(2010, 10, 1, 0, tzinfo=UTC())
            self.assertEqual(
                CourseDetails.update_from_json(self.course.id, jsondetails.__dict__, self.user).start_date,
                jsondetails.start_date
            )
            jsondetails.end_date = datetime.datetime(2011, 10, 1, 0, tzinfo=UTC())
            self.assertEqual(
                CourseDetails.update_from_json(self.course.id, jsondetails.__dict__, self.user).end_date,
                jsondetails.end_date
            )
            jsondetails.course_image_name = "an_image.jpg"
            self.assertEqual(
                CourseDetails.update_from_json(self.course.id, jsondetails.__dict__, self.user).course_image_name,
                jsondetails.course_image_name
            )
            jsondetails.banner_image_name = "an_image.jpg"
            self.assertEqual(
                CourseDetails.update_from_json(self.course.id, jsondetails.__dict__, self.user).banner_image_name,
                jsondetails.banner_image_name
            )
            jsondetails.video_thumbnail_image_name = "an_image.jpg"
            self.assertEqual(
                CourseDetails.update_from_json(self.course.id, jsondetails.__dict__, self.user).video_thumbnail_image_name,
                jsondetails.video_thumbnail_image_name
            )
            jsondetails.language = "hr"
            self.assertEqual(
                CourseDetails.update_from_json(self.course.id, jsondetails.__dict__, self.user).language,
                jsondetails.language
            )
            jsondetails.learning_info = ["test", "test"]
            self.assertEqual(
                CourseDetails.update_from_json(self.course.id, jsondetails.__dict__, self.user).learning_info,
                jsondetails.learning_info
            )
            jsondetails.instructor_info = {
                "instructors": [
                    {
                        "name": "test",
                        "title": "test",
                        "organization": "test",
                        "image": "test",
                        "bio": "test"
                    }
                ]
            }
            self.assertEqual(
                CourseDetails.update_from_json(self.course.id, jsondetails.__dict__, self.user).instructor_info,
                jsondetails.instructor_info
            )

    def test_toggle_pacing_during_course_run(self):
        SelfPacedConfiguration(enabled=True).save()
        self.course.start = datetime.datetime.now()
        self.store.update_item(self.course, self.user.id)

        details = CourseDetails.fetch(self.course.id)
        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, self.course.id):
            updated_details = CourseDetails.update_from_json(
                self.course.id,
                dict(details.__dict__, self_paced=True),
                self.user
            )
        self.assertFalse(updated_details.self_paced)

    @ddt.data(*ABOUT_ATTRIBUTES)
    def test_fetch_about_attribute(self, attribute_name):
        attribute_value = 'test_value'
        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, self.course.id):
            CourseDetails.update_about_item(self.course, attribute_name, attribute_value, self.user.id)
        self.assertEqual(CourseDetails.fetch_about_attribute(self.course.id, attribute_name), attribute_value)

    def test_fetch_about_attribute_error(self):
        attribute_name = 'not_an_about_attribute'
        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, self.course.id):
            CourseDetails.update_about_item(self.course, attribute_name, 'test_value', self.user.id)
        with self.assertRaises(ValueError):
            CourseDetails.fetch_about_attribute(self.course.id, attribute_name)

    def test_fetch_video(self):
        video_value = 'test_video_id'
        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, self.course.id):
            CourseDetails.update_about_video(self.course, video_value, self.user.id)
        self.assertEqual(CourseDetails.fetch_youtube_video_id(self.course.id), video_value)
        video_url = CourseDetails.fetch_video_url(self.course.id)
        self.assertRegexpMatches(video_url, r'http://.*{}'.format(video_value))
