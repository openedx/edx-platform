"""
Tests for functionality in openedx/core/lib/courses.py.
"""


from django.test.utils import override_settings

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from ..courses import course_image_url


class CourseImageTestCase(ModuleStoreTestCase):
    """Tests for course image URLs."""

    def verify_url(self, expected_url, actual_url):
        """
        Helper method for verifying the URL is as expected.
        """
        if not expected_url.startswith("/"):
            expected_url = "/" + expected_url
        assert expected_url == actual_url

    def test_get_image_url(self):
        """Test image URL formatting."""
        course = CourseFactory.create()
        self.verify_url(
            str(course.id.make_asset_key('asset', course.course_image)),
            course_image_url(course)
        )

    def test_non_ascii_image_name(self):
        """ Verify that non-ascii image names are cleaned """
        course_image = 'before_\N{SNOWMAN}_after.jpg'
        course = CourseFactory.create(course_image=course_image)
        self.verify_url(
            str(course.id.make_asset_key('asset', course_image.replace('\N{SNOWMAN}', '_'))),
            course_image_url(course)
        )

    def test_spaces_in_image_name(self):
        """ Verify that image names with spaces in them are cleaned """
        course_image = 'before after.jpg'
        course = CourseFactory.create(course_image='before after.jpg')
        self.verify_url(
            str(course.id.make_asset_key('asset', course_image.replace(" ", "_"))),
            course_image_url(course)
        )

    @override_settings(DEFAULT_COURSE_ABOUT_IMAGE_URL='test.png')
    def test_empty_image_name(self):
        """
        Verify that if a course has empty `course_image`, `course_image_url` returns
        `DEFAULT_COURSE_ABOUT_IMAGE_URL` defined in the settings.
        """
        course = CourseFactory.create(course_image='')
        assert '/static/test.png' == course_image_url(course)

    def test_get_banner_image_url(self):
        """Test banner image URL formatting."""
        banner_image = 'banner_image.jpg'
        course = CourseFactory.create(banner_image=banner_image)
        self.verify_url(
            str(course.id.make_asset_key('asset', banner_image)),
            course_image_url(course, 'banner_image')
        )

    def test_get_video_thumbnail_image_url(self):
        """Test video thumbnail image URL formatting."""
        thumbnail_image = 'thumbnail_image.jpg'
        course = CourseFactory.create(video_thumbnail_image=thumbnail_image)
        self.verify_url(
            str(course.id.make_asset_key('asset', thumbnail_image)),
            course_image_url(course, 'video_thumbnail_image')
        )
