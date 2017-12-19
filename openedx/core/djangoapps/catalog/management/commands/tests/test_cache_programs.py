import json

import httpretty
from django.core.cache import cache
from django.core.management import call_command

from openedx.core.djangoapps.catalog.cache import (
    PROGRAM_CACHE_KEY_TPL,
    SITE_PROGRAM_UUIDS_CACHE_KEY_TPL
)
from openedx.core.djangoapps.catalog.tests.factories import ProgramFactory
from openedx.core.djangoapps.catalog.tests.mixins import CatalogIntegrationMixin
from openedx.core.djangoapps.site_configuration.tests.mixins import SiteMixin
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms
from student.tests.factories import UserFactory


@skip_unless_lms
@httpretty.activate
class TestCachePrograms(CatalogIntegrationMixin, CacheIsolationTestCase, SiteMixin):
    ENABLED_CACHES = ['default']

    def setUp(self):
        super(TestCachePrograms, self).setUp()

        self.catalog_integration = self.create_catalog_integration()
        self.site_domain = 'testsite.com'
        self.set_up_site(
            self.site_domain,
            {
                'COURSE_CATALOG_API_URL': self.catalog_integration.get_internal_api_url().rstrip('/')
            }
        )

        self.list_url = self.catalog_integration.get_internal_api_url().rstrip('/') + '/programs/'
        self.detail_tpl = self.list_url.rstrip('/') + '/{uuid}/'

        self.programs = ProgramFactory.create_batch(3)
        self.uuids = [program['uuid'] for program in self.programs]

    def mock_list(self):
        def list_callback(request, uri, headers):
            expected = {
                'exclude_utm': ['1'],
                'status': ['active', 'retired'],
                'uuids_only': ['1']
            }
            self.assertEqual(request.querystring, expected)

            return (200, headers, json.dumps(self.uuids))

        httpretty.register_uri(
            httpretty.GET,
            self.list_url,
            body=list_callback,
            content_type='application/json'
        )

    def mock_detail(self, uuid, program):
        def detail_callback(request, uri, headers):
            expected = {
                'exclude_utm': ['1'],
            }
            self.assertEqual(request.querystring, expected)

            return (200, headers, json.dumps(program))

        httpretty.register_uri(
            httpretty.GET,
            self.detail_tpl.format(uuid=uuid),
            body=detail_callback,
            content_type='application/json'
        )

    def test_handle(self):
        """
        Verify that the command requests and caches program UUIDs and details.
        """
        # Ideally, this user would be created in the test setup and deleted in
        # the one test case which covers the case where the user is missing. However,
        # that deletion causes "OperationalError: no such table: wiki_attachmentrevision"
        # when run on Jenkins.
        UserFactory(username=self.catalog_integration.service_username)

        programs = {
            PROGRAM_CACHE_KEY_TPL.format(uuid=program['uuid']): program for program in self.programs
        }

        self.mock_list()

        for uuid in self.uuids:
            program = programs[PROGRAM_CACHE_KEY_TPL.format(uuid=uuid)]
            self.mock_detail(uuid, program)

        call_command('cache_programs')

        cached_uuids = cache.get(SITE_PROGRAM_UUIDS_CACHE_KEY_TPL.format(domain=self.site_domain))
        self.assertEqual(
            set(cached_uuids),
            set(self.uuids)
        )

        program_keys = list(programs.keys())
        cached_programs = cache.get_many(program_keys)
        # Verify that the keys were all cache hits.
        self.assertEqual(
            set(cached_programs),
            set(programs)
        )

        # We can't use a set comparison here because these values are dictionaries
        # and aren't hashable. We've already verified that all programs came out
        # of the cache above, so all we need to do here is verify the accuracy of
        # the data itself.
        for key, program in cached_programs.items():
            self.assertEqual(program, programs[key])

    def test_handle_missing_service_user(self):
        """
        Verify that the command raises an exception when run without a service
        user, and that program UUIDs are not cached.
        """
        with self.assertRaises(Exception):
            call_command('cache_programs')

        cached_uuids = cache.get(SITE_PROGRAM_UUIDS_CACHE_KEY_TPL.format(domain=self.site_domain))
        self.assertEqual(cached_uuids, None)

    def test_handle_missing_uuids(self):
        """
        Verify that the command raises an exception when it fails to retrieve
        program UUIDs.
        """
        UserFactory(username=self.catalog_integration.service_username)

        with self.assertRaises(SystemExit) as context:
            call_command('cache_programs')
            self.assertEqual(context.exception.code, 1)

        cached_uuids = cache.get(SITE_PROGRAM_UUIDS_CACHE_KEY_TPL.format(domain=self.site_domain))
        self.assertEqual(cached_uuids, [])

    def test_handle_missing_programs(self):
        """
        Verify that a problem retrieving a program doesn't prevent the command
        from retrieving and caching other programs, but does cause it to exit
        with a non-zero exit code.
        """
        UserFactory(username=self.catalog_integration.service_username)

        all_programs = {
            PROGRAM_CACHE_KEY_TPL.format(uuid=program['uuid']): program for program in self.programs
        }
        partial_programs = {
            PROGRAM_CACHE_KEY_TPL.format(uuid=program['uuid']): program for program in self.programs[:2]
        }

        self.mock_list()

        for uuid in self.uuids[:2]:
            program = partial_programs[PROGRAM_CACHE_KEY_TPL.format(uuid=uuid)]
            self.mock_detail(uuid, program)

        with self.assertRaises(SystemExit) as context:
            call_command('cache_programs')

            self.assertEqual(context.exception.code, 1)

        cached_uuids = cache.get(SITE_PROGRAM_UUIDS_CACHE_KEY_TPL.format(domain=self.site_domain))
        self.assertEqual(
            set(cached_uuids),
            set(self.uuids)
        )

        program_keys = list(all_programs.keys())
        cached_programs = cache.get_many(program_keys)
        # One of the cache keys should result in a cache miss.
        self.assertEqual(
            set(cached_programs),
            set(partial_programs)
        )

        for key, program in cached_programs.items():
            self.assertEqual(program, partial_programs[key])
