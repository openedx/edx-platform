"""
Stub implementation of cs_comments_service for acceptance tests
"""

import re
import urlparse
from .http import StubHttpRequestHandler, StubHttpService


class StubCommentsServiceHandler(StubHttpRequestHandler):

    @property
    def _params(self):
        return urlparse.parse_qs(urlparse.urlparse(self.path).query)

    def do_GET(self):
        pattern_handlers = {
            "/api/v1/users/(?P<user_id>\\d+)/active_threads$": self.do_user_profile,
            "/api/v1/users/(?P<user_id>\\d+)$": self.do_user,
            "/api/v1/search/threads$": self.do_search_threads,
            "/api/v1/threads$": self.do_threads,
            "/api/v1/threads/(?P<thread_id>\\w+)$": self.do_thread,
            "/api/v1/comments/(?P<comment_id>\\w+)$": self.do_comment,
            "/api/v1/(?P<commentable_id>\\w+)/threads$": self.do_commentable,
        }
        if self.match_pattern(pattern_handlers):
            return

        self.send_response(404, content="404 Not Found")

    def match_pattern(self, pattern_handlers):
        path = urlparse.urlparse(self.path).path
        for pattern in pattern_handlers:
            match = re.match(pattern, path)
            if match:
                pattern_handlers[pattern](**match.groupdict())
                return True
        return None

    def do_PUT(self):
        if self.path.startswith('/set_config'):
            return StubHttpRequestHandler.do_PUT(self)
        pattern_handlers = {
            "/api/v1/users/(?P<user_id>\\d+)$": self.do_put_user,
        }
        if self.match_pattern(pattern_handlers):
            return
        self.send_response(204, "")

    def do_put_user(self, user_id):
        self.server.config['default_sort_key'] = self.post_dict.get("default_sort_key", "date")
        self.send_json_response({'username': self.post_dict.get("username"), 'external_id': self.post_dict.get("external_id")})

    def do_DELETE(self):
        pattern_handlers = {
            "/api/v1/comments/(?P<comment_id>\\w+)$": self.do_delete_comment
        }
        if self.match_pattern(pattern_handlers):
            return
        self.send_json_response({})

    def do_user(self, user_id):
        response = {
            "id": user_id,
            "default_sort_key": self.server.config.get("default_sort_key", "date"),
            "upvoted_ids": [],
            "downvoted_ids": [],
            "subscribed_thread_ids": [],
        }
        if 'course_id' in self._params:
            response.update({
                "threads_count": 1,
                "comments_count": 2
            })
        self.send_json_response(response)

    def do_user_profile(self, user_id):
        if 'active_threads' in self.server.config:
            user_threads = self.server.config['active_threads'][:]
            params = self._params
            page = int(params.get("page", ["1"])[0])
            per_page = int(params.get("per_page", ["20"])[0])
            num_pages = max(len(user_threads) - 1, 1) / per_page + 1
            user_threads = user_threads[(page - 1) * per_page:page * per_page]
            self.send_json_response({
                "collection": user_threads,
                "page": page,
                "num_pages": num_pages
            })
        else:
            self.send_response(404, content="404 Not Found")

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
        threads = self.server.config.get('threads', {})
        threads_data = threads.values()
        self.send_json_response({"collection": threads_data, "page": 1, "num_pages": 1})

    def do_search_threads(self):
        self.send_json_response(self.server.config.get('search_result', {}))

    def do_comment(self, comment_id):
        # django_comment_client calls GET comment before doing a DELETE, so that's what this is here to support.
        if comment_id in self.server.config.get('comments', {}):
            comment = self.server.config['comments'][comment_id]
            self.send_json_response(comment)

    def do_delete_comment(self, comment_id):
        """Handle comment deletion. Returns a JSON representation of the
        deleted comment."""
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
