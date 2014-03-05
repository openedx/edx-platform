"""
Stub implementation of cs_comments_service for acceptance tests
"""

from datetime import datetime
import re
import urlparse
from .http import StubHttpRequestHandler, StubHttpService


class StubCommentsServiceHandler(StubHttpRequestHandler):
    def do_GET(self):
        pattern_handlers = {
            "/api/v1/users/(?P<user_id>\\d+)$": self.do_user,
            "/api/v1/threads$": self.do_threads,
            "/api/v1/threads/(?P<thread_id>\\w+)$": self.do_thread,
        }
        path = urlparse.urlparse(self.path).path
        for pattern in pattern_handlers:
            match = re.match(pattern, path)
            if match:
                pattern_handlers[pattern](**match.groupdict())
                return

        self.send_response(404, content="404 Not Found")

    def do_PUT(self):
        self.send_response(204, "")

    def do_user(self, user_id):
        self.send_json_response({
            "id": user_id,
            "upvoted_ids": [],
            "downvoted_ids": [],
            "subscribed_thread_ids": [],
        })

    def do_thread(self, thread_id):
        match = re.search("(?P<num>\\d+)_responses", thread_id)
        resp_total = int(match.group("num")) if match else 0
        thread = {
            "id": thread_id,
            "commentable_id": "dummy",
            "type": "thread",
            "title": "Thread title",
            "body": "Thread body",
            "created_at": datetime.utcnow().isoformat(),
            "unread_comments_count": 0,
            "comments_count": resp_total,
            "votes": {"up_count": 0},
            "abuse_flaggers": [],
            "closed": "closed" in thread_id,
        }
        params = urlparse.parse_qs(urlparse.urlparse(self.path).query)
        if "recursive" in params and params["recursive"][0] == "True":
            thread["resp_total"] = resp_total
            thread["children"] = []
            resp_skip = int(params.get("resp_skip", ["0"])[0])
            resp_limit = int(params.get("resp_limit", ["10000"])[0])
            num_responses = min(resp_limit, resp_total - resp_skip)
            self.log_message("Generating {} children; resp_limit={} resp_total={} resp_skip={}".format(num_responses, resp_limit, resp_total, resp_skip))
            for i in range(num_responses):
                response_id = str(resp_skip + i)
                thread["children"].append({
                    "id": str(response_id),
                    "type": "comment",
                    "body": response_id,
                    "created_at": datetime.utcnow().isoformat(),
                    "votes": {"up_count": 0},
                    "abuse_flaggers": [],
                })
        self.send_json_response(thread)

    def do_threads(self):
        self.send_json_response({"collection": [], "page": 1, "num_pages": 1})


class StubCommentsService(StubHttpService):
    HANDLER_CLASS = StubCommentsServiceHandler
