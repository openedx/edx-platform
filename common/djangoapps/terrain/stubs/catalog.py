"""
Stub implementation of catalog service for acceptance tests
"""
import re
import urlparse

from .http import StubHttpRequestHandler, StubHttpService


class StubCatalogServiceHandler(StubHttpRequestHandler):  # pylint: disable=missing-docstring

    def do_GET(self):  # pylint: disable=invalid-name, missing-docstring
        pattern_handlers = {
            r'/api/v1/course_runs/(?P<course_id>[^/+]+(/|\+)[^/+]+(/|\+)[^/?]+)/$': self.get_course_run,
        }

        if self.match_pattern(pattern_handlers):
            return

        self.send_response(404, content="404 Not Found")

    def match_pattern(self, pattern_handlers):
        """
        Find the correct handler method given the path info from the HTTP request.
        """
        path = urlparse.urlparse(self.path).path
        for pattern in pattern_handlers:
            match = re.match(pattern, path)
            if match:
                pattern_handlers[pattern](*match.groups())
                return True
        return None

    def get_course_run(self, course_id):
        """
        Stubs a catalog course run endpoint.
        """
        course_run = self.server.config.get('course_run.{}'.format(course_id), [])
        self.send_json_response(course_run)


class StubCatalogService(StubHttpService):  # pylint: disable=missing-docstring
    HANDLER_CLASS = StubCatalogServiceHandler
