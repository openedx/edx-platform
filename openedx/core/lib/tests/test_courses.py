"""
Tests for functionality in openedx/core/lib/courses.py.
"""

import ddt
from django.test.utils import override_settings
from nose.plugins.attrib import attr

from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from ..courses import course_image_url


@attr('shard_2')
@ddt.ddt
class CourseImageTestCase(ModuleStoreTestCase):
    """Tests for course image URLs."""

    def verify_url(self, expected_url, actual_url):
        """
        Helper method for verifying the URL is as expected.
        """
        if not expected_url.startswith("/"):
            expected_url = "/" + expected_url
        self.assertEquals(expected_url, actual_url)

    def test_get_image_url(self):
        """Test image URL formatting."""
        course = CourseFactory.create()
        self.verify_url(
            unicode(course.id.make_asset_key('asset', course.course_image)),
            course_image_url(course)
        )

    def test_non_ascii_image_name(self):
        """ Verify that non-ascii image names are cleaned """
        course_image = u'before_\N{SNOWMAN}_after.jpg'
        course = CourseFactory.create(course_image=course_image)
        self.verify_url(
            unicode(course.id.make_asset_key('asset', course_image.replace(u'\N{SNOWMAN}', '_'))),
            course_image_url(course)
        )

    def test_spaces_in_image_name(self):
        """ Verify that image names with spaces in them are cleaned """
        course_image = u'before after.jpg'
        course = CourseFactory.create(course_image=u'before after.jpg')
        self.verify_url(
            unicode(course.id.make_asset_key('asset', course_image.replace(" ", "_"))),
            course_image_url(course)
        )

    @override_settings(DEFAULT_COURSE_ABOUT_IMAGE_URL='test.png')
    @override_settings(STATIC_URL='static/')
    @ddt.data(ModuleStoreEnum.Type.split, ModuleStoreEnum.Type.mongo)
    def test_empty_image_name(self, default_store):
        """
        Verify that if a course has empty `course_image`, `course_image_url` returns
        `DEFAULT_COURSE_ABOUT_IMAGE_URL` defined in the settings.
        """
        course = CourseFactory.create(course_image='', default_store=default_store)
        self.assertEquals(
            'static/test.png',
            course_image_url(course),
        )

    def test_get_hero_image_url(self):
        """Test hero image URL formatting."""
        hero_image = u'hero_image.jpg'
        course = CourseFactory.create(hero_image=hero_image)
        self.verify_url(
            unicode(course.id.make_asset_key('asset', hero_image)),
            course_image_url(course, 'hero_image')
        )

    def test_get_thumbnail_image_url(self):
        """Test thumbnail image URL formatting."""
        thumbnail_image = u'thumbnail_image.jpg'
        course = CourseFactory.create(thumbnail_image=thumbnail_image)
        self.verify_url(
            unicode(course.id.make_asset_key('asset', thumbnail_image)),
            course_image_url(course, 'thumbnail_image')
        )
