import json

import httpretty
from django.core.cache import cache
from django.core.management import CommandError, call_command

from openedx.core.djangoapps.catalog.cache import (
    COURSE_PROGRAMS_CACHE_KEY_TPL,
    PATHWAY_CACHE_KEY_TPL,
    PROGRAM_CACHE_KEY_TPL,
    SITE_PATHWAY_IDS_CACHE_KEY_TPL,
    SITE_PROGRAM_UUIDS_CACHE_KEY_TPL
)
from openedx.core.djangoapps.catalog.tests.factories import PathwayFactory, ProgramFactory
from openedx.core.djangoapps.catalog.tests.mixins import CatalogIntegrationMixin
from openedx.core.djangoapps.site_configuration.tests.mixins import SiteMixin
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms
from student.tests.factories import UserFactory

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


@skip_unless_lms
@httpretty.activate
class TestCachePrograms(CatalogIntegrationMixin, CacheIsolationTestCase, ModuleStoreTestCase, SiteMixin):
    ENABLED_CACHES = ['default']

    def setUp(self):
        super(TestCachePrograms, self).setUp()

        httpretty.httpretty.reset()

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
        self.pathway_url = self.catalog_integration.get_internal_api_url().rstrip('/') + '/pathways/'
        self.course_run_url = self.catalog_integration.get_internal_api_url().rstrip('/') + '/course_runs/'

        self.programs = ProgramFactory.create_batch(3)
        self.pathways = PathwayFactory.create_batch(3)

        # Build the course run list to look like the course run api. We want to start from the program
        # list so that the courses are associated with the programs.
        course_run_dict = {}
        for program in self.programs:
            program_uuid = program['uuid']
            for course in program['courses']:
                for course_run in course['course_runs']:
                    course_run_key = course_run['key']
                    if course_run_key in course_run_dict:
                        course_run_dict[course_run_key]['programs'] += {'uuid': program_uuid}
                    else:
                        course_run_dict[course_run_key] = {'key': course_run_key, 'programs': [{'uuid': program_uuid}]}
        self.course_runs = course_run_dict.values()

        for pathway in self.pathways:
            self.programs += pathway['programs']

        self.uuids = [program['uuid'] for program in self.programs]

        # add some of the previously created programs to some pathways
        self.pathways[0]['programs'].extend([self.programs[0], self.programs[1]])
        self.pathways[1]['programs'].append(self.programs[0])

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

    def mock_pathways(self, pathways, page_number=1, final=True):
        """
        Mock the data for discovery's credit pathways endpoint
        """
        def pathways_callback(request, uri, headers):  # pylint: disable=unused-argument
            """
            Mocks response
            """

            expected = {
                'exclude_utm': ['1'],
                'page': [str(page_number)],
            }
            self.assertEqual(request.querystring, expected)

            body = {
                'count': len(pathways),
                'next': None if final else 'more',  # we don't actually parse this value
                'prev': None,
                'results': pathways
            }

            return (200, headers, json.dumps(body))

        # NOTE: httpretty does not properly match against query strings here (using match_querystring arg)
        # as such, it does not actually look at the query parameters (for page num), but returns items in a LIFO order.
        # this means that for multiple pages, you must call this function starting from the last page.
        # we do assert the page number query param above, however
        httpretty.register_uri(
            httpretty.GET,
            self.pathway_url,
            body=pathways_callback,
            content_type='application/json',
        )

    def mock_courses(self, course_runs, page_number=1, final=True):
        """
        Mock the data for discovery's course_run endpoint
        """
        def course_run_callback(request, uri, headers):  # pylint: disable=unused-argument
            """
            Mocks response
            """
            expected = {
                'exclude_utm': ['1'],
                'page': [str(page_number)],
            }
            self.assertEqual(request.querystring, expected)

            body = {
                'count': len(course_runs),
                'next': None if final else 'more',  # we don't actually parse this value
                'prev': None,
                'results': course_runs
            }

            return (200, headers, json.dumps(body))

        httpretty.register_uri(
            httpretty.GET,
            self.course_run_url,
            body=course_run_callback,
            content_type='application/json',
        )

    def test_handle_programs(self):
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
        self.mock_pathways(self.pathways)
        self.mock_courses(self.course_runs)

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
            # cached programs have a pathways field added to them, remove before comparing
            del program['pathway_ids']
            self.assertEqual(program, programs[key])

    def test_handle_pathways(self):
        """
        Verify that the command requests and caches credit pathways
        """

        UserFactory(username=self.catalog_integration.service_username)

        programs = {
            PROGRAM_CACHE_KEY_TPL.format(uuid=program['uuid']): program for program in self.programs
        }

        pathways = {
            PATHWAY_CACHE_KEY_TPL.format(id=pathway['id']): pathway for pathway in self.pathways
        }

        self.mock_list()
        self.mock_pathways(self.pathways)
        self.mock_courses(self.course_runs)

        for uuid in self.uuids:
            program = programs[PROGRAM_CACHE_KEY_TPL.format(uuid=uuid)]
            self.mock_detail(uuid, program)

        call_command('cache_programs')

        cached_pathway_keys = cache.get(SITE_PATHWAY_IDS_CACHE_KEY_TPL.format(domain=self.site_domain))
        pathway_keys = pathways.keys()
        self.assertEqual(
            set(cached_pathway_keys),
            set(pathway_keys)
        )

        cached_pathways = cache.get_many(pathway_keys)
        self.assertEqual(
            set(cached_pathways),
            set(pathways)
        )

        # We can't use a set comparison here because these values are dictionaries
        # and aren't hashable. We've already verified that all pathways came out
        # of the cache above, so all we need to do here is verify the accuracy of
        # the data itself.
        for key, pathway in cached_pathways.items():
            # cached pathways store just program uuids instead of the full programs, transform before comparing
            pathways[key]['program_uuids'] = [program['uuid'] for program in pathways[key]['programs']]
            del pathways[key]['programs']

            self.assertEqual(pathway, pathways[key])

    def test_pathways_multiple_pages(self):
        """
        Verify that the command properly caches credit pathways when multiple pages are returned from its endpoint
        """
        UserFactory(username=self.catalog_integration.service_username)
        new_pathways = PathwayFactory.create_batch(40)
        for new_pathway in new_pathways:
            new_pathway['programs'] = []
        pathways = self.pathways + new_pathways

        programs = {
            PROGRAM_CACHE_KEY_TPL.format(uuid=program['uuid']): program for program in self.programs
        }

        self.mock_list()
        self.mock_courses(self.course_runs)
        for uuid in self.uuids:
            program = programs[PROGRAM_CACHE_KEY_TPL.format(uuid=uuid)]
            self.mock_detail(uuid, program)

        # mock 3 pages of credit pathways, starting at the last
        self.mock_pathways(pathways[40:], page_number=3, final=True)
        self.mock_pathways(pathways[20:40], page_number=2, final=False)
        self.mock_pathways(pathways[:20], page_number=1, final=False)

        call_command('cache_programs')

        pathways_dict = {
            PATHWAY_CACHE_KEY_TPL.format(id=pathway['id']): pathway for pathway in pathways
        }
        pathway_keys = pathways_dict.keys()

        cached_pathway_keys = cache.get(SITE_PATHWAY_IDS_CACHE_KEY_TPL.format(domain=self.site_domain))
        self.assertEqual(
            set(cached_pathway_keys),
            set(pathway_keys)
        )

        cached_pathways = cache.get_many(pathway_keys)
        self.assertEqual(
            set(cached_pathways),
            set(pathways_dict)
        )

        # We can't use a set comparison here because these values are dictionaries
        # and aren't hashable. We've already verified that all pathways came out
        # of the cache above, so all we need to do here is verify the accuracy of
        # the data itself.
        for key, pathway in cached_pathways.items():
            # cached pathways store just program uuids instead of the full programs, transform before comparing
            pathways_dict[key]['program_uuids'] = [program['uuid'] for program in pathways_dict[key]['programs']]
            del pathways_dict[key]['programs']

            self.assertEqual(pathway, pathways_dict[key])

    def test_handle_courses(self):
        """
        Verify that the command requests and caches course to program uuids
        """

        UserFactory(username=self.catalog_integration.service_username)

        programs = {
            PROGRAM_CACHE_KEY_TPL.format(uuid=program['uuid']): program for program in self.programs
        }

        courses = {
            COURSE_PROGRAMS_CACHE_KEY_TPL.format(course_run_id=course['key']):
            [pu['uuid'] for pu in course['programs']]
            for course in self.course_runs
        }

        self.mock_list()
        self.mock_pathways(self.pathways)
        self.mock_courses(self.course_runs)

        for uuid in self.uuids:
            program = programs[PROGRAM_CACHE_KEY_TPL.format(uuid=uuid)]
            self.mock_detail(uuid, program)

        call_command('cache_programs')

        cached_courses = cache.get_many(list(courses.keys()))
        self.assertEqual(
            set(cached_courses),
            set(courses)
        )

        # We can't use a set comparison here because these values are dictionaries
        # and aren't hashable. We've already verified that all pathways came out
        # of the cache above, so all we need to do here is verify the accuracy of
        # the data itself.
        for key, course in cached_courses.items():
            self.assertEqual(course, courses[key])

    def test_handle_courses_multiple_pages(self):
        """
        Verify that the command requests and caches course to program uuids
        """

        UserFactory(username=self.catalog_integration.service_username)

        programs = {
            PROGRAM_CACHE_KEY_TPL.format(uuid=program['uuid']): program for program in self.programs
        }

        courses = {
            COURSE_PROGRAMS_CACHE_KEY_TPL.format(course_run_id=course['key']):
            [pu['uuid'] for pu in course['programs']]
            for course in self.course_runs
        }

        self.mock_list()
        self.mock_pathways(self.pathways)
        # mock 3 pages of course_runs, starting at the last
        self.mock_courses(self.course_runs[20:], page_number=3, final=True)
        self.mock_courses(self.course_runs[10:20], page_number=2, final=False)
        self.mock_courses(self.course_runs[:10], page_number=1, final=False)

        for uuid in self.uuids:
            program = programs[PROGRAM_CACHE_KEY_TPL.format(uuid=uuid)]
            self.mock_detail(uuid, program)

        call_command('cache_programs')

        cached_courses = cache.get_many(list(courses.keys()))
        self.assertEqual(
            set(cached_courses),
            set(courses)
        )

        # We can't use a set comparison here because these values are dictionaries
        # and aren't hashable. We've already verified that all pathways came out
        # of the cache above, so all we need to do here is verify the accuracy of
        # the data itself.
        for key, course in cached_courses.items():
            self.assertEqual(course, courses[key])

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

        with self.assertRaises(CommandError) as context:
            call_command('cache_programs')
        self.assertEqual(str(context.exception), "Caching program information failed")

        cached_uuids = cache.get(SITE_PROGRAM_UUIDS_CACHE_KEY_TPL.format(domain=self.site_domain))
        self.assertEqual(cached_uuids, [])

    def test_handle_missing_pathways(self):
        """
        Verify that the command raises an exception when it fails to retrieve pathways.
        """
        UserFactory(username=self.catalog_integration.service_username)

        programs = {
            PROGRAM_CACHE_KEY_TPL.format(uuid=program['uuid']): program for program in self.programs
        }

        self.mock_list()

        for uuid in self.uuids:
            program = programs[PROGRAM_CACHE_KEY_TPL.format(uuid=uuid)]
            self.mock_detail(uuid, program)

        with self.assertRaises(CommandError) as context:
            call_command('cache_programs')
        self.assertEqual(str(context.exception), "Caching program information failed")

        cached_pathways = cache.get(SITE_PATHWAY_IDS_CACHE_KEY_TPL.format(domain=self.site_domain))
        self.assertEqual(cached_pathways, [])

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

        with self.assertRaises(CommandError) as context:
            call_command('cache_programs')

        self.assertEqual(str(context.exception), "Caching program information failed")

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
            # cached programs have a pathways field added to them, remove before comparing
            del program['pathway_ids']
            self.assertEqual(program, partial_programs[key])

    def test_handle_missing_course_runs(self):
        """
        Verify that the command raises an exception when it fails to retrieve course runs.
        """
        UserFactory(username=self.catalog_integration.service_username)

        self.mock_list()
        # Only mock out the first page of courses. Pages 2 and 3 will be missing.
        self.mock_courses(self.course_runs[:10], page_number=1, final=False)

        with self.assertRaises(CommandError) as context:
            call_command('cache_programs')

        self.assertEqual(str(context.exception), "Caching program information failed")
