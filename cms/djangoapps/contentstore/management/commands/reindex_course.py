""" Management command to update courses' search index """


import logging
from textwrap import dedent

from django.core.management import BaseCommand, CommandError
from elasticsearch import exceptions
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import CourseLocator
from search.search_engine_base import SearchEngine

from cms.djangoapps.contentstore.courseware_index import CourseAboutSearchIndexer, CoursewareSearchIndexer
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order

from .prompt import query_yes_no


class Command(BaseCommand):
    """
    Command to re-index courses

    Examples:

        ./manage.py reindex_course <course_id_1> <course_id_2> ... - reindexes courses with provided keys
        ./manage.py reindex_course --all - reindexes all available courses
        ./manage.py reindex_course --setup - reindexes all courses for devstack setup
    """
    help = dedent(__doc__)
    CONFIRMATION_PROMPT = "Re-indexing all courses might be a time consuming operation. Do you want to continue?"

    def add_arguments(self, parser):
        parser.add_argument('course_ids',
                            nargs='*',
                            metavar='course_id')
        parser.add_argument('--all',
                            action='store_true',
                            help='Reindex all courses')
        parser.add_argument('--setup',
                            action='store_true',
                            help='Reindex all courses on developers stack setup')

    def _parse_course_key(self, raw_value):
        """ Parses course key from string """
        try:
            result = CourseKey.from_string(raw_value)
        except InvalidKeyError:
            raise CommandError("Invalid course_key: '%s'." % raw_value)  # lint-amnesty, pylint: disable=raise-missing-from

        if not isinstance(result, CourseLocator):
            raise CommandError(f"Argument {raw_value} is not a course key")

        return result

    def handle(self, *args, **options):
        """
        By convention set by Django developers, this method actually executes command's actions.
        So, there could be no better docstring than emphasize this once again.
        """
        course_ids = options['course_ids']
        all_option = options['all']
        setup_option = options['setup']
        index_all_courses_option = all_option or setup_option

        if (not len(course_ids) and not index_all_courses_option) or (len(course_ids) and index_all_courses_option):  # lint-amnesty, pylint: disable=len-as-condition
            raise CommandError("reindex_course requires one or more <course_id>s OR the --all or --setup flags.")

        store = modulestore()

        if index_all_courses_option:
            index_names = (CoursewareSearchIndexer.INDEX_NAME, CourseAboutSearchIndexer.INDEX_NAME)
            if setup_option:
                for index_name in index_names:
                    try:
                        searcher = SearchEngine.get_search_engine(index_name)
                    except exceptions.ElasticsearchException as exc:
                        logging.exception('Search Engine error - %s', exc)
                        return

                    index_exists = searcher._es.indices.exists(index=index_name)  # pylint: disable=protected-access

                    index_mapping = searcher._es.indices.get_mapping(  # pylint: disable=protected-access
                        index=index_name,
                    ) if index_exists else {}

                    if index_exists and index_mapping:
                        return

            # if reindexing is done during devstack setup step, don't prompt the user
            if setup_option or query_yes_no(self.CONFIRMATION_PROMPT, default="no"):
                # in case of --setup or --all, get the list of course keys from all courses
                # that are stored in the modulestore
                course_keys = [course.id for course in modulestore().get_courses()]
            else:
                return
        else:
            # in case course keys are provided as arguments
            course_keys = list(map(self._parse_course_key, course_ids))

        for course_key in course_keys:
            try:
                CoursewareSearchIndexer.do_course_reindex(store, course_key)
            except Exception as exc:  # lint-amnesty, pylint: disable=broad-except
                logging.exception('Error indexing course %s due to the error: %s', course_key, exc)
