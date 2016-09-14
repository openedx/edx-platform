"""
Script for importing courseware from git/xml into a mongo modulestore
"""

import logging

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _

import dashboard.git_import
from dashboard.git_import import GitImportError
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.xml import XMLModuleStore

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Pull a git repo and import into the mongo based content database.
    """

    # Translators: A git repository is a place to store a grouping of
    # versioned files. A branch is a sub grouping of a repository that
    # has a specific version of the repository. A modulestore is the database used
    # to store the courses for use on the Web site.
    help = ('Usage: '
            'git_add_course repository_url [directory to check out into] [repository_branch] '
            '\n{0}'.format(_('Import the specified git repository and optional branch into the '
                             'modulestore and optionally specified directory.')))

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('repository_url')
        parser.add_argument('--directory_path', action='store')
        parser.add_argument('--repository_branch', action='store')

    def handle(self, *args, **options):
        """Check inputs and run the command"""

        if isinstance(modulestore, XMLModuleStore):
            raise CommandError('This script requires a mongo module store')

        rdir_arg = None
        branch = None
        if options['directory_path']:
            rdir_arg = options['directory_path']
        if options['repository_branch']:
            branch = options['repository_branch']

        try:
            dashboard.git_import.add_repo(options['repository_url'], rdir_arg, branch)
        except GitImportError as ex:
            raise CommandError(str(ex))
