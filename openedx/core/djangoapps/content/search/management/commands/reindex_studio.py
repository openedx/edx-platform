"""
Command to build or re-build the search index for courses (in Studio, i.e. Draft
mode), in Meilisearch.

See also cms/djangoapps/contentstore/management/commands/reindex_course.py which
indexes LMS (published) courses in ElasticSearch.
"""
from django.core.management import BaseCommand, CommandError

from ... import api


class Command(BaseCommand):
    """
    Build or re-build the search index for courses and libraries (in Studio, i.e. Draft mode)

    This is experimental and not recommended for production use.
    """

    def add_arguments(self, parser):
        parser.add_argument('--experimental', action='store_true')
        parser.set_defaults(experimental=False)

    def handle(self, *args, **options):
        """
        Build a new search index for Studio, containing content from courses and libraries
        """
        if not api.is_meilisearch_enabled():
            raise CommandError("Meilisearch is not enabled. Please set MEILISEARCH_ENABLED to True in your settings.")

        if not options["experimental"]:
            raise CommandError(
                "This command is experimental and not recommended for production. "
                "Use the --experimental argument to acknowledge and run it."
            )

        api.rebuild_index(self.stdout.write)
