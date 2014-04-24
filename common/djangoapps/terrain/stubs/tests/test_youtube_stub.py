"""
Unit test for stub YouTube implementation.
"""

import unittest
import requests
from ..youtube import StubYouTubeService


class StubYouTubeServiceTest(unittest.TestCase):

    def setUp(self):
        self.server = StubYouTubeService()
        self.url = "http://127.0.0.1:{0}/".format(self.server.port)
        self.server.config['time_to_response'] = 0.0
        self.addCleanup(self.server.shutdown)

    def test_unused_url(self):
        response = requests.get(self.url + 'unused_url')
        self.assertEqual("Unused url", response.content)

    def test_video_url(self):
        response = requests.get(
            self.url + 'test_youtube/OEoXaMPEzfM?v=2&alt=jsonc&callback=callback_func'
        )

        # YouTube metadata for video `OEoXaMPEzfM` states that duration is 116.
        self.assertEqual(
            'callback_func({"data": {"duration": 116, "message": "I\'m youtube.", "id": "OEoXaMPEzfM"}})',
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
            ]), response.content
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
            ]), response.content
        )

    def test_transcript_not_found(self):
        response = requests.get(self.url + 'test_transcripts_youtube/some_id')
        self.assertEqual(404, response.status_code)
