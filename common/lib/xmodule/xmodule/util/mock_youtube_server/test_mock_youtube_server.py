"""
Test for Mock_Youtube_Server
"""
import unittest
import threading
import requests
from mock_youtube_server import MockYoutubeServer


class MockYoutubeServerTest(unittest.TestCase):
    '''
    A mock version of the YouTube provider server that listens on a local
    port and responds with jsonp.

    Used for lettuce BDD tests in lms/courseware/features/video.feature
    '''

    def setUp(self):

        # Create the server
        server_port = 8034
        server_host = '127.0.0.1'
        address = (server_host, server_port)
        self.server = MockYoutubeServer(address, )
        self.server.time_to_response = 0.5
        # Start the server in a separate daemon thread
        server_thread = threading.Thread(target=self.server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

    def tearDown(self):

        # Stop the server, freeing up the port
        self.server.shutdown()

    def test_request(self):
        """
        Tests that Youtube server processes request with right program
        path,  and responses with incorrect signature.
        """
        # GET request

        # unused url
        response = requests.get(
            'http://127.0.0.1:8034/some url',
        )
        self.assertEqual("Unused url", response.content)

        # video player test url, callback shoud be presented in url params
        response = requests.get(
            'http://127.0.0.1:8034/test_youtube/OEoXaMPEzfM?v=2&alt=jsonc&callback=callback_func',
        )
        self.assertEqual("""callback_func({"message": "I\'m youtube."})""", response.content)

        # transcripts test url
        response = requests.get(
            'http://127.0.0.1:8034/test_transcripts_youtube/t__eq_exist',
        )
        self.assertEqual(
            '<?xml version="1.0" encoding="utf-8" ?><transcript><text start="1.0" dur="1.0">Equal transcripts</text></transcript>',
            response.content
        )

        # transcripts test url
        response = requests.get(
            'http://127.0.0.1:8034/test_transcripts_youtube/t_neq_exist',
        )
        self.assertEqual(
            '<?xml version="1.0" encoding="utf-8" ?><transcript><text start="1.1" dur="5.5">Transcripts sample, different that on server</text></transcript>',
            response.content
        )

        # transcripts test url, not trans_exist youtube_id, so 404 should be returned
        response = requests.get(
            'http://127.0.0.1:8034/test_transcripts_youtube/some_id',
        )
        self.assertEqual(404, response.status_code)
