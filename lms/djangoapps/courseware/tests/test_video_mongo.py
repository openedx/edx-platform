# -*- coding: utf-8 -*-
"""Video xmodule tests in mongo."""

from . import BaseTestXmodule


class TestVideo(BaseTestXmodule):
    """Integration tests: web client + mongo."""

    TEMPLATE_NAME = "i4x://edx/templates/video/default"
    DATA = '<video  youtube="0.75:JMD_ifUUfsU,1.0:OEoXaMPEzfM,1.25:AKqURZnYqpk,1.50:DYpADpL7jAY"/>'

    def test_handle_ajax_dispatch(self):
        responses = {
            user.username: self.clients[user.username].post(
                self.get_url('whatever'),
                {},
                HTTP_X_REQUESTED_WITH='XMLHttpRequest'
            ) for user in self.users
        }

        self.assertEqual(
            set([
                response.status_code
                for _, response in responses.items()
                ]).pop(),
            404)
