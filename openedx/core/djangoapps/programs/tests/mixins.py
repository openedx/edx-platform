"""Mixins for use during testing."""
import json

import httpretty

from openedx.core.djangoapps.programs.models import ProgramsApiConfig


class ProgramsApiConfigMixin(object):
    """Utilities for working with Programs configuration during testing."""

    DEFAULTS = {
        'enabled': True,
        'api_version_number': 1,
        'internal_service_url': 'http://internal.programs.org/',
        'public_service_url': 'http://public.programs.org/',
        'authoring_app_js_path': '/path/to/js',
        'authoring_app_css_path': '/path/to/css',
        'cache_ttl': 0,
        'enable_student_dashboard': True,
        'enable_studio_tab': True,
    }

    def create_config(self, **kwargs):
        """Creates a new ProgramsApiConfig with DEFAULTS, updated with any provided overrides."""
        fields = dict(self.DEFAULTS, **kwargs)
        ProgramsApiConfig(**fields).save()

        return ProgramsApiConfig.current()


class ProgramsDataMixin(object):
    """Mixin mocking Programs API URLs and providing fake data for testing."""
    PROGRAM_NAMES = [
        'Test Program A',
        'Test Program B',
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
            {
                'id': 1,
                'name': PROGRAM_NAMES[0],
                'subtitle': 'A program used for testing purposes',
                'category': 'xseries',
                'status': 'unpublished',
                'marketing_slug': '',
                'organizations': [
                    {
                        'display_name': 'Test Organization A',
                        'key': 'organization-a'
                    }
                ],
                'course_codes': [
                    {
                        'display_name': 'Test Course A',
                        'key': 'course-a',
                        'organization': {
                            'display_name': 'Test Organization A',
                            'key': 'organization-a'
                        },
                        'run_modes': [
                            {
                                'course_key': COURSE_KEYS[0],
                                'mode_slug': 'verified',
                                'sku': '',
                                'start_date': '2015-11-05T07:39:02.791741Z',
                                'run_key': 'fall'
                            },
                            {
                                'course_key': COURSE_KEYS[1],
                                'mode_slug': 'verified',
                                'sku': '',
                                'start_date': '2015-11-05T07:39:02.791741Z',
                                'run_key': 'winter'
                            }
                        ]
                    },
                    {
                        'display_name': 'Test Course B',
                        'key': 'course-b',
                        'organization': {
                            'display_name': 'Test Organization A',
                            'key': 'organization-a'
                        },
                        'run_modes': [
                            {
                                'course_key': COURSE_KEYS[2],
                                'mode_slug': 'verified',
                                'sku': '',
                                'start_date': '2015-11-05T07:39:02.791741Z',
                                'run_key': 'fall'
                            },
                            {
                                'course_key': COURSE_KEYS[3],
                                'mode_slug': 'verified',
                                'sku': '',
                                'start_date': '2015-11-05T07:39:02.791741Z',
                                'run_key': 'winter'
                            }
                        ]
                    }
                ],
                'created': '2015-10-26T17:52:32.861000Z',
                'modified': '2015-11-18T22:21:30.826365Z'
            },
            {
                'id': 2,
                'name': PROGRAM_NAMES[1],
                'subtitle': 'Another program used for testing purposes',
                'category': 'xseries',
                'status': 'unpublished',
                'marketing_slug': '',
                'organizations': [
                    {
                        'display_name': 'Test Organization B',
                        'key': 'organization-b'
                    }
                ],
                'course_codes': [
                    {
                        'display_name': 'Test Course C',
                        'key': 'course-c',
                        'organization': {
                            'display_name': 'Test Organization B',
                            'key': 'organization-b'
                        },
                        'run_modes': [
                            {
                                'course_key': COURSE_KEYS[4],
                                'mode_slug': 'verified',
                                'sku': '',
                                'start_date': '2015-11-05T07:39:02.791741Z',
                                'run_key': 'fall'
                            },
                            {
                                'course_key': COURSE_KEYS[5],
                                'mode_slug': 'verified',
                                'sku': '',
                                'start_date': '2015-11-05T07:39:02.791741Z',
                                'run_key': 'winter'
                            }
                        ]
                    },
                    {
                        'display_name': 'Test Course D',
                        'key': 'course-d',
                        'organization': {
                            'display_name': 'Test Organization B',
                            'key': 'organization-b'
                        },
                        'run_modes': [
                            {
                                'course_key': COURSE_KEYS[6],
                                'mode_slug': 'verified',
                                'sku': '',
                                'start_date': '2015-11-05T07:39:02.791741Z',
                                'run_key': 'fall'
                            },
                            {
                                'course_key': COURSE_KEYS[7],
                                'mode_slug': 'verified',
                                'sku': '',
                                'start_date': '2015-11-05T07:39:02.791741Z',
                                'run_key': 'winter'
                            }
                        ]
                    }
                ],
                'created': '2015-10-26T19:59:03.064000Z',
                'modified': '2015-10-26T19:59:18.536000Z'
            }
        ]
    }

    def mock_programs_api(self, data=None, status_code=200):
        """Utility for mocking out Programs API URLs."""
        self.assertTrue(httpretty.is_enabled(), msg='httpretty must be enabled to mock Programs API calls.')

        url = ProgramsApiConfig.current().internal_api_url.strip('/') + '/programs/'

        if data is None:
            data = self.PROGRAMS_API_RESPONSE

        body = json.dumps(data)

        httpretty.reset()
        httpretty.register_uri(httpretty.GET, url, body=body, content_type='application/json', status=status_code)
