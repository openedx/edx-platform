# coding: utf-8
"""
Acceptance tests for licensing of the Video module
"""
from __future__ import unicode_literals
from nose.plugins.attrib import attr
from openedx.tests.acceptance.tests.studio.base_studio_test import StudioCourseTest

#from openedx.tests.acceptance.tests.helpers import UniqueCourseTest
from openedx.tests.acceptance.pages.studio.overview import CourseOutlinePage
from openedx.tests.acceptance.pages.lms.courseware import CoursewarePage
from openedx.tests.acceptance.fixtures.course import XBlockFixtureDesc


@attr(shard=2)
class VideoLicenseTest(StudioCourseTest):
    """
    Tests for video module-level licensing (that is, setting the license,
    for a specific video module, to All Rights Reserved or Creative Commons)
    """
    def setUp(self):  # pylint: disable=arguments-differ
        super(VideoLicenseTest, self).setUp()

        self.lms_courseware = CoursewarePage(
            self.browser,
            self.course_id,
        )
        self.studio_course_outline = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

    # used by StudioCourseTest.setUp()
    def populate_course_fixture(self, course_fixture):
        """
        Create a course with a single chapter.
        That chapter has a single section.
        That section has a single vertical.
        That vertical has a single video element.
        """
        video_block = XBlockFixtureDesc('video', "Test Video")
        vertical = XBlockFixtureDesc('vertical', "Test Vertical")
        vertical.add_children(video_block)
        sequential = XBlockFixtureDesc('sequential', "Test Section")
        sequential.add_children(vertical)
        chapter = XBlockFixtureDesc('chapter', "Test Chapter")
        chapter.add_children(sequential)
        self.course_fixture.add_children(chapter)

    def test_empty_license(self):
        """
        When I visit the LMS courseware,
        I can see that the video is present
        but it has no license displayed by default.
        """
        self.lms_courseware.visit()
        video = self.lms_courseware.q(css=".vert .xblock .video")
        self.assertTrue(video.is_present())
        video_license = self.lms_courseware.q(css=".vert .xblock.xmodule_VideoModule .xblock-license")
        self.assertFalse(video_license.is_present())

    def test_arr_license(self):
        """
        When I edit a video element in Studio,
        I can set an "All Rights Reserved" license on that video element.
        When I visit the LMS courseware,
        I can see that the video is present
        and that it has "All Rights Reserved" displayed for the license.
        """
        self.studio_course_outline.visit()
        subsection = self.studio_course_outline.section_at(0).subsection_at(0)
        subsection.expand_subsection()
        unit = subsection.unit_at(0)
        container_page = unit.go_to()
        container_page.edit()
        video = [xb for xb in container_page.xblocks if xb.name == "Test Video"][0]
        video.open_advanced_tab()
        video.set_license('all-rights-reserved')
        video.save_settings()
        container_page.publish_action.click()

        self.lms_courseware.visit()
        video = self.lms_courseware.q(css=".vert .xblock .video")
        self.assertTrue(video.is_present())
        video_license_css = ".vert .xblock.xmodule_VideoModule .xblock-license"
        self.lms_courseware.wait_for_element_presence(
            video_license_css, "Video module license block is present"
        )
        video_license = self.lms_courseware.q(css=video_license_css)
        self.assertEqual(video_license.text[0], "© All Rights Reserved")

    def test_cc_license(self):
        """
        When I edit a video element in Studio,
        I can set a "Creative Commons" license on that video element.
        When I visit the LMS courseware,
        I can see that the video is present
        and that it has "Some Rights Reserved" displayed for the license.
        """
        self.studio_course_outline.visit()
        subsection = self.studio_course_outline.section_at(0).subsection_at(0)
        subsection.expand_subsection()
        unit = subsection.unit_at(0)
        container_page = unit.go_to()
        container_page.edit()
        video = [xb for xb in container_page.xblocks if xb.name == "Test Video"][0]
        video.open_advanced_tab()
        video.set_license('creative-commons')
        video.save_settings()
        container_page.publish_action.click()

        self.lms_courseware.visit()
        video = self.lms_courseware.q(css=".vert .xblock .video")
        self.assertTrue(video.is_present())
        video_license_css = ".vert .xblock.xmodule_VideoModule .xblock-license"
        self.lms_courseware.wait_for_element_presence(
            video_license_css, "Video module license block is present"
        )
        video_license = self.lms_courseware.q(css=video_license_css)
        self.assertIn("Some Rights Reserved", video_license.text[0])
