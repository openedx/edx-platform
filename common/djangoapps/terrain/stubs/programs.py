"""
Stub implementation of programs service for acceptance tests
"""
import re
import urlparse

from .http import StubHttpRequestHandler, StubHttpService


class StubProgramsServiceHandler(StubHttpRequestHandler):  # pylint: disable=missing-docstring

    def do_GET(self):  # pylint: disable=invalid-name, missing-docstring
        pattern_handlers = {
            r'/api/v1/programs/$': self.get_programs_list,
            r'/api/v1/programs/(\d+)/$': self.get_program_details,
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

    def get_programs_list(self):
        """
        Stubs the programs list endpoint.
        """
        programs = self.server.config.get('programs', [])
        self.send_json_response(programs)

    def get_program_details(self, program_id):
        """
        Stubs a program details endpoint.
        """
        program = self.server.config.get('programs.{}'.format(program_id), [])
        self.send_json_response(program)


class StubProgramsService(StubHttpService):  # pylint: disable=missing-docstring
    HANDLER_CLASS = StubProgramsServiceHandler
