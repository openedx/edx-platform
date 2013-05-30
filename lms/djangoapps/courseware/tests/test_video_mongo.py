# -*- coding: utf-8 -*-
"""Video xmodule tests in mongo."""

import json

from . import BaseTestXmodule


class TestVideo(BaseTestXmodule):
    """Integration tests: web client + mongo."""

    TEMPLATE_NAME = "i4x://edx/templates/video/default"
    DATA = '<video  youtube="0.75:JMD_ifUUfsU,1.0:OEoXaMPEzfM,1.25:AKqURZnYqpk,1.50:DYpADpL7jAY"/>'

    def test_handle_ajax_correct_dispatch(self):
        responses = {
            user.username: self.clients[user.username].post(
                self.get_url('goto_position'),
                {'position': 10},
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            for user in self.users
        }

        response_contents = {
            username: json.loads(response.content) for username, response in
            responses.items()
        }

        self.assertTrue(
            all([
                content['success']
                for _, content in response_contents.items()
                ]))

    def test_handle_ajax_incorrect_dispatch(self):
        responses = {
            user.username: self.clients[user.username].post(
                self.get_url('whatever'),
                {},
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            for user in self.users
        }

        self.assertEqual(
            set([
                response.status_code
                for _, response in responses.items()
                ]).pop(),
            404)
