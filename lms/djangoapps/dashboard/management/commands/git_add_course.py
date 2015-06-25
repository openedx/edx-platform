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

    def handle(self, *args, **options):
        """Check inputs and run the command"""

        if isinstance(modulestore, XMLModuleStore):
            raise CommandError('This script requires a mongo module store')

        if len(args) < 1:
            raise CommandError('This script requires at least one argument, '
                               'the git URL')

        if len(args) > 3:
            raise CommandError('Expected no more than three '
                               'arguments; received {0}'.format(len(args)))

        rdir_arg = None
        branch = None

        if len(args) > 1:
            rdir_arg = args[1]
        if len(args) > 2:
            branch = args[2]

        try:
            dashboard.git_import.add_repo(args[0], rdir_arg, branch)
        except GitImportError as ex:
            raise CommandError(str(ex))
