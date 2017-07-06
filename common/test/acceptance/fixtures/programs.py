"""
Tools to create programs-related data for use in bok choy tests.
"""
import json

import requests

from common.test.acceptance.fixtures import PROGRAMS_STUB_URL
from common.test.acceptance.fixtures.config import ConfigModelFixture


class ProgramsFixture(object):
    """
    Interface to set up mock responses from the Programs stub server.
    """
    def install_programs(self, programs, is_list=True):
        """Sets the response data for Programs API endpoints."""
        if is_list:
            key = 'programs'
            api_result = {'results': programs}
        else:
            program = programs[0]
            key = 'programs.{}'.format(program['id'])
            api_result = program

        requests.put(
            '{}/set_config'.format(PROGRAMS_STUB_URL),
            data={key: json.dumps(api_result)},
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
            'program_details_enabled': is_enabled,
        }).install()
