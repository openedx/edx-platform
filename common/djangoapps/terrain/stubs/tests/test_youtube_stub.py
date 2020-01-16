"""
Unit test for stub YouTube implementation.
"""


import unittest

import requests

from ..youtube import StubYouTubeService


class StubYouTubeServiceTest(unittest.TestCase):

    def setUp(self):
        super(StubYouTubeServiceTest, self).setUp()
        self.server = StubYouTubeService()
        self.url = "http://127.0.0.1:{0}/".format(self.server.port)
        self.server.config['time_to_response'] = 0.0
        self.addCleanup(self.server.shutdown)

    def test_unused_url(self):
        response = requests.get(self.url + 'unused_url')
        self.assertEqual(b"Unused url", response.content)

    @unittest.skip('Failing intermittently due to inconsistent responses from YT. See TE-871')
    def test_video_url(self):
        response = requests.get(
            self.url + 'test_youtube/OEoXaMPEzfM?v=2&alt=jsonc&callback=callback_func'
        )

        # YouTube metadata for video `OEoXaMPEzfM` states that duration is 116.
        self.assertEqual(
            b'callback_func({"data": {"duration": 116, "message": "I\'m youtube.", "id": "OEoXaMPEzfM"}})',
            response.content
        )

    def test_transcript_url_equal(self):
        response = requests.get(
            self.url + 'test_transcripts_youtube/t__eq_exist'
        )

        self.assertEqual(
            "".join([
                '<?xml version="1.0" encoding="utf-8" ?>',
                '<transcript><text start="1.0" dur="1.0">',
                'Equal transcripts</text></transcript>'
            ]).encode('utf-8'), response.content
        )

    def test_transcript_url_not_equal(self):
        response = requests.get(
            self.url + 'test_transcripts_youtube/t_neq_exist',
        )

        self.assertEqual(
            "".join([
                '<?xml version="1.0" encoding="utf-8" ?>',
                '<transcript><text start="1.1" dur="5.5">',
                'Transcripts sample, different that on server',
                '</text></transcript>'
            ]).encode('utf-8'), response.content
        )

    def test_transcript_not_found(self):
        response = requests.get(self.url + 'test_transcripts_youtube/some_id')
        self.assertEqual(404, response.status_code)

    def test_reset_configuration(self):

        reset_config_url = self.url + 'del_config'

        # add some configuration data
        self.server.config['test_reset'] = 'This is a reset config test'

        # reset server configuration
        response = requests.delete(reset_config_url)
        self.assertEqual(response.status_code, 200)

        # ensure that server config dict is empty after successful reset
        self.assertEqual(self.server.config, {})
