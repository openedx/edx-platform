"""
This command downloads the translations for the XBlocks that are installed.
"""
import shutil
import subprocess
import os.path

from django.conf import settings

from django.core.management.base import BaseCommand

from ...api import get_xblocks_entry_points


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose|-v',
            action='store_true',
            default=False,
            dest='verbose',
            help='Verbose output.'
        )

        parser.add_argument(
            '--list|-l',
            action='store_true',
            default=False,
            dest='list',
            help='List plugins module names.'
        )

    def handle(self, *args, **options):
        # Remove previous translations
        for dir_name in os.listdir(settings.PLUGINS_TRANSLATIONS_ROOT):
            dir_path = os.path.join(settings.PLUGINS_TRANSLATIONS_ROOT, dir_name)

            if os.path.isdir(dir_path):
                shutil.rmtree(dir_path, ignore_errors=True)

        xblock_module_names = set()
        for entry_point in get_xblocks_entry_points():
            xblock = entry_point.resolve()
            module_import_path = xblock.__module__
            parent_module, _rest = module_import_path.split('.', maxsplit=1)
            if parent_module == 'xmodule':
                if options['verbose']:
                    self.stdout.write(f'INFO: Skipped edx-platform XBlock "{entry_point.name}" '
                                      f'in module={module_import_path}')
            else:
                xblock_module_names.add(parent_module)

        sorted_xblock_module_names = list(sorted(xblock_module_names))

        if options['list']:
            self.stdout.write('\n'.join(sorted_xblock_module_names))
        else:
            xblock_atlas_args_list = [
                f'translations/edx-platform-plugins/{module_name}:{module_name}'
                for module_name in sorted_xblock_module_names
            ]

            subprocess.run(
                [
                    'atlas', 'pull',
                    '--repository=Zeit-Labs/openedx-translations',
                    '--branch=plugins-fix'
                ] + xblock_atlas_args_list,
                cwd=settings.PLUGINS_TRANSLATIONS_ROOT,
            )
