import unittest
from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.content import ContentStore
from xmodule.modulestore import Location


class Content:
    def __init__(self, location, content_type):
        self.location = location
        self.content_type = content_type


class ContentTest(unittest.TestCase):
    def test_thumbnail_none(self):
        # We had a bug where a thumbnail location of None was getting transformed into a Location tuple, with
        # all elements being None. It is important that the location be just None for rendering.
        content = StaticContent('loc', 'name', 'content_type', 'data', None, None, None)
        self.assertIsNone(content.thumbnail_location)

        content = StaticContent('loc', 'name', 'content_type', 'data')
        self.assertIsNone(content.thumbnail_location)

    def test_static_url_generation_from_courseid(self):
        url = StaticContent.convert_legacy_static_url_with_course_id('images_course_image.jpg', 'foo/bar/bz')
        self.assertEqual(url, '/c4x/foo/bar/asset/images_course_image.jpg')

    def test_generate_thumbnail_image(self):
        contentStore = ContentStore()
        content = Content(Location(u'c4x', u'edX', u'800', u'asset', u'monsters__.jpg'), None)
        (thumbnail_content, thumbnail_file_location) = contentStore.generate_thumbnail(content)
        self.assertIsNone(thumbnail_content)
        self.assertEqual(Location(u'c4x', u'edX', u'800', u'thumbnail', u'monsters__.jpg'), thumbnail_file_location)

    def test_compute_location(self):
        # We had a bug that __ got converted into a single _. Make sure that substitution of INVALID_CHARS (like space)
        # still happen.
        asset_location = StaticContent.compute_location('edX', '400', 'subs__1eo_jXvZnE .srt.sjson')
        self.assertEqual(Location(u'c4x', u'edX', u'400', u'asset', u'subs__1eo_jXvZnE_.srt.sjson', None), asset_location)
