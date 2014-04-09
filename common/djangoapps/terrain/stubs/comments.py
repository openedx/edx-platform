"""
Stub implementation of cs_comments_service for acceptance tests
"""

import re
import urlparse
from .http import StubHttpRequestHandler, StubHttpService


class StubCommentsServiceHandler(StubHttpRequestHandler):
    def do_GET(self):
        pattern_handlers = {
            "/api/v1/users/(?P<user_id>\\d+)$": self.do_user,
            "/api/v1/threads$": self.do_threads,
            "/api/v1/threads/(?P<thread_id>\\w+)$": self.do_thread,
            "/api/v1/comments/(?P<comment_id>\\w+)$": self.do_comment,
            "/api/v1/(?P<commentable_id>\\w+)/threads$": self.do_commentable,
        }
        path = urlparse.urlparse(self.path).path
        for pattern in pattern_handlers:
            match = re.match(pattern, path)
            if match:
                pattern_handlers[pattern](**match.groupdict())
                return

        self.send_response(404, content="404 Not Found")

    def do_PUT(self):
        if self.path.startswith('/set_config'):
            return StubHttpRequestHandler.do_PUT(self)
        self.send_response(204, "")

    def do_DELETE(self):
        self.send_json_response({})

    def do_user(self, user_id):
        self.send_json_response({
            "id": user_id,
            "upvoted_ids": [],
            "downvoted_ids": [],
            "subscribed_thread_ids": [],
        })

    def do_thread(self, thread_id):
        if thread_id in self.server.config.get('threads', {}):
            thread = self.server.config['threads'][thread_id].copy()
            params = urlparse.parse_qs(urlparse.urlparse(self.path).query)
            if "recursive" in params and params["recursive"][0] == "True":
                thread.setdefault('children', [])
                resp_total = thread.setdefault('resp_total', len(thread['children']))
                resp_skip = int(params.get("resp_skip", ["0"])[0])
                resp_limit = int(params.get("resp_limit", ["10000"])[0])
                thread['children'] = thread['children'][resp_skip:(resp_skip + resp_limit)]
            self.send_json_response(thread)
        else:
            self.send_response(404, content="404 Not Found")

    def do_threads(self):
        self.send_json_response({"collection": [], "page": 1, "num_pages": 1})

    def do_comment(self, comment_id):
        # django_comment_client calls GET comment before doing a DELETE, so that's what this is here to support.
        if comment_id in self.server.config.get('comments', {}):
            comment = self.server.config['comments'][comment_id]
            self.send_json_response(comment)

    def do_commentable(self, commentable_id):
        self.send_json_response({
            "collection": [
                thread
                for thread in self.server.config.get('threads', {}).values()
                if thread.get('commentable_id') == commentable_id
            ],
            "page": 1,
            "num_pages": 1,
        })


class StubCommentsService(StubHttpService):
    HANDLER_CLASS = StubCommentsServiceHandler
