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
    def test_generate_thumbnail_nonimage(self):
        contentStore = ContentStore()
        content = Content(Location(u'c4x', u'mitX', u'800', u'asset', u'monsters.jpg'), None)
        (thumbnail_content, thumbnail_file_location) = contentStore.generate_thumbnail(content)
        self.assertIsNone(thumbnail_content)
        self.assertEqual(Location(u'c4x', u'mitX', u'800', u'thumbnail', u'monsters.jpg'), thumbnail_file_location)