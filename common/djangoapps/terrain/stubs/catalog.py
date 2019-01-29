"""
Stub implementation of catalog service for acceptance tests
"""
# pylint: disable=invalid-name, missing-docstring
import re
import urlparse

from .http import StubHttpRequestHandler, StubHttpService


class StubCatalogServiceHandler(StubHttpRequestHandler):

    def do_GET(self):
        pattern_handlers = {
            r'/api/v1/programs/$': self.program_list,
            r'/api/v1/programs/([0-9a-f-]+)/$': self.program_detail,
            r'/api/v1/program_types/$': self.program_types,
            r'/api/v1/pathways/$': self.pathways,
            r'/api/v1/course_runs/$': self.course_runs,
        }

        if self.match_pattern(pattern_handlers):
            return

        self.send_response(404, content='404 Not Found')

    def match_pattern(self, pattern_handlers):
        """
        Find the correct handler method given the path info from the HTTP request.
        """
        path = urlparse.urlparse(self.path).path
        for pattern, handler in pattern_handlers.items():
            match = re.match(pattern, path)
            if match:
                handler(*match.groups())
                return True

    def program_list(self):
        """Stub the catalog's program list endpoint."""
        programs = self.server.config.get('catalog.programs', [])
        self.send_json_response(programs)

    def program_detail(self, program_uuid):
        """Stub the catalog's program detail endpoint."""
        program = self.server.config.get('catalog.programs.' + program_uuid)
        self.send_json_response(program)

    def program_types(self):
        program_types = self.server.config.get('catalog.programs_types', [])
        self.send_json_response(program_types)

    def pathways(self):
        pathways = self.server.config.get('catalog.pathways', [])
        self.send_json_response(pathways)

    def course_runs(self):
        course_runs = self.server.config.get('catalog.course_runs', {'results': [], 'next': None})
        self.send_json_response(course_runs)


class StubCatalogService(StubHttpService):
    HANDLER_CLASS = StubCatalogServiceHandler
