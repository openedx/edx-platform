"""
Download the translations via atlas for the XBlocks.
"""

from django.core.management.base import BaseCommand, CommandError

from openedx.core.djangoapps.plugins.i18n_api import ATLAS_ARGUMENTS
from xmodule.modulestore import api as xmodule_api

from ...translation import xblocks_atlas_pull


class Command(BaseCommand):
    """
    Pull the XBlock translations via atlas for the XBlocks.

    For detailed information about atlas pull options check the atlas documentation:

     - https://github.com/openedx/openedx-atlas
    """

    def add_arguments(self, parser):
        for argument in ATLAS_ARGUMENTS:
            parser.add_argument(*argument.get_args(), **argument.get_kwargs())

        parser.add_argument(
            '--verbose|-v',
            action='store_true',
            default=False,
            dest='verbose',
            help='Verbose output using `--verbose` argument for `atlas pull`.',
        )

    def handle(self, *args, **options):
        xblock_translations_root = xmodule_api.get_python_locale_root()
        if list(xblock_translations_root.listdir()):
            raise CommandError(f'"{xblock_translations_root}" should be empty before running atlas pull.')

        atlas_pull_options = []

        for argument in ATLAS_ARGUMENTS:
            option_value = options.get(argument.dest)
            if option_value is not None:
                atlas_pull_options += [argument.flag, option_value]

        if options['verbose']:
            atlas_pull_options += ['--verbose']
        else:
            atlas_pull_options += ['--silent']

        xblocks_atlas_pull(pull_options=atlas_pull_options)
