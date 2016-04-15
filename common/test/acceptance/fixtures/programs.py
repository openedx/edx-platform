"""
Tools to create programs-related data for use in bok choy tests.
"""
from collections import namedtuple
import json

import factory
import requests

from . import PROGRAMS_STUB_URL
from .config import ConfigModelFixture


FakeProgram = namedtuple('FakeProgram', ['name', 'status', 'org_key', 'course_id'])


class Program(factory.Factory):
    """
    Factory for stubbing program resources from the Programs API (v1).
    """
    class Meta(object):
        model = dict

    id = factory.Sequence(lambda n: n)  # pylint: disable=invalid-name
    name = 'dummy-program-name'
    subtitle = 'dummy-program-subtitle'
    category = 'xseries'
    status = 'unpublished'
    marketing_slug = factory.Sequence(lambda n: 'slug-{}'.format(n))  # pylint: disable=unnecessary-lambda
    organizations = []
    course_codes = []
    banner_image_urls = {}


class Organization(factory.Factory):
    """
    Factory for stubbing nested organization resources from the Programs API (v1).
    """
    class Meta(object):
        model = dict

    key = 'dummyX'
    display_name = 'dummy-org-display-name'


class CourseCode(factory.Factory):
    """
    Factory for stubbing nested course code resources from the Programs API (v1).
    """
    class Meta(object):
        model = dict

    display_name = 'dummy-org-display-name'
    run_modes = []


class RunMode(factory.Factory):
    """
    Factory for stubbing nested run mode resources from the Programs API (v1).
    """
    class Meta(object):
        model = dict

    course_key = 'org/course/run'
    mode_slug = 'verified'


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
            run_mode = RunMode(course_key=program.course_id)
            course_code = CourseCode(run_modes=[run_mode])
            org = Organization(key=program.org_key)

            program = Program(
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
