"""
Tools to create programs-related data for use in bok choy tests.
"""
from collections import namedtuple
import json

import requests

from . import PROGRAMS_STUB_URL
from .config import ConfigModelFixture
from openedx.core.djangoapps.programs.tests import factories


FakeProgram = namedtuple('FakeProgram', ['name', 'status', 'org_key', 'course_id'])


class ProgramsFixture(object):
    """
    Interface to set up mock responses from the Programs stub server.
    """

    def install_programs(self, fake_programs):
        """
        Sets the response data for the programs list endpoint.

        At present, `fake_programs` must be a iterable of FakeProgram named tuples.
        """
        programs = []
        for program in fake_programs:
            run_mode = factories.RunMode(course_key=program.course_id)
            course_code = factories.CourseCode(run_modes=[run_mode])
            org = factories.Organization(key=program.org_key)

            program = factories.Program(
                name=program.name,
                status=program.status,
                organizations=[org],
                course_codes=[course_code]
            )
            programs.append(program)

        api_result = {'results': programs}

        requests.put(
            '{}/set_config'.format(PROGRAMS_STUB_URL),
            data={'programs': json.dumps(api_result)},
        )


class ProgramsConfigMixin(object):
    """Mixin providing a method used to configure the programs feature."""
    def set_programs_api_configuration(self, is_enabled=False, api_version=1, api_url=PROGRAMS_STUB_URL,
                                       js_path='/js', css_path='/css'):
        """Dynamically adjusts the Programs config model during tests."""
        ConfigModelFixture('/config/programs', {
            'enabled': is_enabled,
            'api_version_number': api_version,
            'internal_service_url': api_url,
            'public_service_url': api_url,
            'authoring_app_js_path': js_path,
            'authoring_app_css_path': css_path,
            'cache_ttl': 0,
            'enable_student_dashboard': is_enabled,
            'enable_studio_tab': is_enabled,
            'enable_certification': is_enabled,
            'xseries_ad_enabled': is_enabled,
            'program_listing_enabled': is_enabled,
        }).install()
