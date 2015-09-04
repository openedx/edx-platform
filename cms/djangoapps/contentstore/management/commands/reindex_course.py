""" Management command to update courses' search index """
import logging
from django.core.management import BaseCommand, CommandError
from optparse import make_option
from textwrap import dedent

from contentstore.courseware_index import CoursewareSearchIndexer
from search.search_engine_base import SearchEngine
from elasticsearch import exceptions

from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import CourseLocator

from .prompt import query_yes_no

from xmodule.modulestore.django import modulestore


class Command(BaseCommand):
    """
    Command to re-index courses

    Examples:

        ./manage.py reindex_course <course_id_1> <course_id_2> - reindexes courses with keys course_id_1 and course_id_2
        ./manage.py reindex_course --all - reindexes all available courses
        ./manage.py reindex_course --setup - reindexes all courses for devstack setup
    """
    help = dedent(__doc__)

    can_import_settings = True

    args = "<course_id course_id ...>"

    all_option = make_option('--all',
                             action='store_true',
                             dest='all',
                             default=False,
                             help='Reindex all courses')

    setup_option = make_option('--setup',
                               action='store_true',
                               dest='setup',
                               default=False,
                               help='Reindex all courses on developers stack setup')

    option_list = BaseCommand.option_list + (all_option, setup_option)

    CONFIRMATION_PROMPT = u"Re-indexing all courses might be a time consuming operation. Do you want to continue?"

    def _parse_course_key(self, raw_value):
        """ Parses course key from string """
        try:
            result = CourseKey.from_string(raw_value)
        except InvalidKeyError:
            raise CommandError("Invalid course_key: '%s'." % raw_value)

        if not isinstance(result, CourseLocator):
            raise CommandError(u"Argument {0} is not a course key".format(raw_value))

        return result

    def handle(self, *args, **options):
        """
        By convention set by Django developers, this method actually executes command's actions.
        So, there could be no better docstring than emphasize this once again.
        """
        all_option = options.get('all', False)
        setup_option = options.get('setup', False)
        index_all_courses_option = all_option or setup_option

        if len(args) == 0 and not index_all_courses_option:
            raise CommandError(u"reindex_course requires one or more arguments: <course_id>")

        store = modulestore()

        if index_all_courses_option:
            index_name = CoursewareSearchIndexer.INDEX_NAME
            doc_type = CoursewareSearchIndexer.DOCUMENT_TYPE
            if setup_option:
                try:
                    # try getting the ElasticSearch engine
                    searcher = SearchEngine.get_search_engine(index_name)
                except exceptions.ElasticsearchException as exc:
                    logging.exception('Search Engine error - %s', unicode(exc))
                    return

                index_exists = searcher._es.indices.exists(index=index_name)  # pylint: disable=protected-access
                doc_type_exists = searcher._es.indices.exists_type(  # pylint: disable=protected-access
                    index=index_name,
                    doc_type=doc_type
                )

                index_mapping = searcher._es.indices.get_mapping(  # pylint: disable=protected-access
                    index=index_name,
                    doc_type=doc_type
                ) if index_exists and doc_type_exists else {}

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
            course_keys = map(self._parse_course_key, args)

        for course_key in course_keys:
            CoursewareSearchIndexer.do_course_reindex(store, course_key)
