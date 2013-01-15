from django.test.testcases import TestCase
from cache_toolbox.core import get_cached_content, set_cached_content
import mock

class CachingTestCase(TestCase):
#   Tests for https://edx.lighthouseapp.com/projects/102637/tickets/112-updating-asset-does-not-refresh-the-cached-copy
    def test_put_and_get(self):
        mockAsset = mock.Mock()
        mockLocation = mock.Mock()
        mockLocation.category = u'thumbnail'
        mockLocation.name = u'monsters.jpg'
        mockLocation.course = u'800'
        mockLocation.tag = u'c4x'
        mockLocation.org = u'mitX'
        mockLocation.revision = None
        mockAsset.location = mockLocation
        set_cached_content(mockAsset)
        cachedAsset = get_cached_content(mockLocation)
