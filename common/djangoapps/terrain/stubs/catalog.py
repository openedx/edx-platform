"""
Stub implementation of catalog service for acceptance tests
"""
# pylint: disable=invalid-name


import re

import six.moves.urllib.parse

from .http import StubHttpRequestHandler, StubHttpService


class StubCatalogServiceHandler(StubHttpRequestHandler):  # lint-amnesty, pylint: disable=missing-class-docstring

    def do_GET(self):  # lint-amnesty, pylint: disable=missing-function-docstring
        pattern_handlers = {
            r'/api/v1/programs/$': self.program_list,
            r'/api/v1/programs/([0-9a-f-]+)/$': self.program_detail,
            r'/api/v1/program_types/$': self.program_types,
            r'/api/v1/pathways/$': self.pathways
        }

        if self.match_pattern(pattern_handlers):
            return

        self.send_response(404, content='404 Not Found')

    def match_pattern(self, pattern_handlers):
        """
        Find the correct handler method given the path info from the HTTP request.
        """
        path = six.moves.urllib.parse.urlparse(self.path).path
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


class StubCatalogService(StubHttpService):
    HANDLER_CLASS = StubCatalogServiceHandler
