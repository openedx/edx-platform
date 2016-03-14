"""
Tools to create programs-related data for use in bok choy tests.
"""

import json
import factory
import requests

from . import PROGRAMS_STUB_URL


class Program(factory.Factory):
    """
    Factory for stubbing program resources from the Programs API (v1).
    """
    class Meta(object):
        model = dict

    id = factory.Sequence(lambda n: n)  # pylint: disable=invalid-name
    name = "dummy-program-name"
    subtitle = "dummy-program-subtitle"
    category = "xseries"
    status = "unpublished"
    organizations = []
    course_codes = []


class Organization(factory.Factory):
    """
    Factory for stubbing nested organization resources from the Programs API (v1).
    """
    class Meta(object):
        model = dict

    key = "dummyX"
    display_name = "dummy-org-display-name"


class ProgramsFixture(object):
    """
    Interface to set up mock responses from the Programs stub server.
    """

    def install_programs(self, program_values):
        """
        Sets the response data for the programs list endpoint.

        At present, `program_values` needs to be a sequence of sequences of (program_name, org_key).
        """
        programs = []
        for program_name, org_key in program_values:
            org = Organization(key=org_key)
            program = Program(name=program_name, organizations=[org])
            programs.append(program)

        api_result = {'results': programs}

        requests.put(
            '{}/set_config'.format(PROGRAMS_STUB_URL),
            data={'programs': json.dumps(api_result)},
        )
