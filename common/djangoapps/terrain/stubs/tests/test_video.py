"""
Unit tests for Video stub server implementation.
"""


import unittest

import requests
from django.conf import settings

from common.djangoapps.terrain.stubs.video_source import VideoSourceHttpService

HLS_MANIFEST_TEXT = """
#EXTM3U
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=264787,RESOLUTION=1280x720
history_264kbit/history_264kbit.m3u8
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=328415,RESOLUTION=1920x1080
history_328kbit/history_328kbit.m3u8
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=70750,RESOLUTION=640x360
history_70kbit/history_70kbit.m3u8
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=148269,RESOLUTION=960x540
history_148kbit/history_148kbit.m3u8
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=41276,RESOLUTION=640x360
history_41kbit/history_41kbit.m3u8
"""


class StubVideoServiceTest(unittest.TestCase):
    """
    Test cases for the video stub service.
    """
    def setUp(self):
        """
        Start the stub server.
        """
        super(StubVideoServiceTest, self).setUp()
        self.server = VideoSourceHttpService()
        self.server.config['root_dir'] = '{}/data/video'.format(settings.TEST_ROOT)
        self.addCleanup(self.server.shutdown)

    def test_get_hls_manifest(self):
        """
        Verify that correct hls manifest is received.
        """
        response = requests.get("http://127.0.0.1:{port}/hls/history.m3u8".format(port=self.server.port))
        self.assertTrue(response.ok)
        self.assertEqual(response.text, HLS_MANIFEST_TEXT.lstrip())
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], '*')
