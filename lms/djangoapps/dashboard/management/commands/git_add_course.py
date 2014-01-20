"""
Script for importing courseware from git/xml into a mongo modulestore
"""

import os
import re
import StringIO
import subprocess
import logging

from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _

import dashboard.git_import
from dashboard.git_import import GitImportError
from dashboard.models import CourseImportLog
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.xml import XMLModuleStore

log = logging.getLogger(__name__)

class Command(BaseCommand):
    """
    Pull a git repo and import into the mongo based content database.
    """

    help = _('Import the specified git repository into the '
             'modulestore and directory')

    def handle(self, *args, **options):
        """Check inputs and run the command"""

        if isinstance(modulestore, XMLModuleStore):
            raise CommandError('This script requires a mongo module store')

        if len(args) < 1:
            raise CommandError('This script requires at least one argument, '
                               'the git URL')

        if len(args) > 2:
            raise CommandError('This script requires no more than two '
                               'arguments')

        rdir_arg = None

        if len(args) > 1:
            rdir_arg = args[1]

        try:
            dashboard.git_import.add_repo(args[0], rdir_arg)
        except GitImportError as ex:
            raise CommandError(str(ex))
