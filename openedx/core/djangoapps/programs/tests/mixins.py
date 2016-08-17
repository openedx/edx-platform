"""Mixins for use during testing."""
import json

import httpretty

from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.programs.tests import factories


class ProgramsApiConfigMixin(object):
    """Utilities for working with Programs configuration during testing."""

    DEFAULTS = {
        'enabled': True,
        'api_version_number': 1,
        'internal_service_url': 'http://internal.programs.org/',
        'public_service_url': 'http://public.programs.org/',
        'cache_ttl': 0,
        'enable_studio_tab': True,
        'enable_certification': True,
        'program_listing_enabled': True,
        'program_details_enabled': True,
        'marketing_path': 'foo',
    }

    def create_programs_config(self, **kwargs):
        """Creates a new ProgramsApiConfig with DEFAULTS, updated with any provided overrides."""
        fields = dict(self.DEFAULTS, **kwargs)
        ProgramsApiConfig(**fields).save()

        return ProgramsApiConfig.current()


class ProgramsDataMixin(object):
    """Mixin mocking Programs API URLs and providing fake data for testing.

    NOTE: This mixin is DEPRECATED. Tests should create and manage their own data.
    """
    PROGRAM_NAMES = [
        'Test Program A',
        'Test Program B',
        'Test Program C',
    ]

    COURSE_KEYS = [
        'organization-a/course-a/fall',
        'organization-a/course-a/winter',
        'organization-a/course-b/fall',
        'organization-a/course-b/winter',
        'organization-b/course-c/fall',
        'organization-b/course-c/winter',
        'organization-b/course-d/fall',
        'organization-b/course-d/winter',
    ]

    PROGRAMS_API_RESPONSE = {
        'results': [
            factories.Program(
                id=1,
                name=PROGRAM_NAMES[0],
                organizations=[factories.Organization()],
                course_codes=[
                    factories.CourseCode(run_modes=[
                        factories.RunMode(course_key=COURSE_KEYS[0]),
                        factories.RunMode(course_key=COURSE_KEYS[1]),
                    ]),
                    factories.CourseCode(run_modes=[
                        factories.RunMode(course_key=COURSE_KEYS[2]),
                        factories.RunMode(course_key=COURSE_KEYS[3]),
                    ]),
                ]
            ),
            factories.Program(
                id=2,
                name=PROGRAM_NAMES[1],
                organizations=[factories.Organization()],
                course_codes=[
                    factories.CourseCode(run_modes=[
                        factories.RunMode(course_key=COURSE_KEYS[4]),
                        factories.RunMode(course_key=COURSE_KEYS[5]),
                    ]),
                    factories.CourseCode(run_modes=[
                        factories.RunMode(course_key=COURSE_KEYS[6]),
                        factories.RunMode(course_key=COURSE_KEYS[7]),
                    ]),
                ]
            ),
            factories.Program(
                id=3,
                name=PROGRAM_NAMES[2],
                organizations=[factories.Organization()],
                course_codes=[
                    factories.CourseCode(run_modes=[
                        factories.RunMode(course_key=COURSE_KEYS[7]),
                    ]),
                ]
            ),
        ]
    }

    def mock_programs_api(self, data=None, program_id='', status_code=200):
        """Utility for mocking out Programs API URLs."""
        self.assertTrue(httpretty.is_enabled(), msg='httpretty must be enabled to mock Programs API calls.')

        url = ProgramsApiConfig.current().internal_api_url.strip('/') + '/programs/'
        if program_id:
            url += '{}/'.format(str(program_id))

        if data is None:
            data = self.PROGRAMS_API_RESPONSE

        body = json.dumps(data)

        httpretty.reset()
        httpretty.register_uri(httpretty.GET, url, body=body, content_type='application/json', status=status_code)
