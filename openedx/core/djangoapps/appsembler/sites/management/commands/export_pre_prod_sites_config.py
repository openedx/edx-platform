"""
Used for moving pre-prod candidate configs and theme updates to production after release upgrade.
"""

import json

from django.core.management import BaseCommand

from openedx.core.djangoapps.appsembler.sites.utils import get_active_sites


class Command(BaseCommand):
    help = 'Export configurations of active sites from pre-production candidate servers in jsonlines.org format.'

    def add_arguments(self, parser):
        parser.add_argument(
            'export_file',
            help='The path of the `.jsonl` file to be exported.',
            type=str,
        )

    def handle(self, *args, **options):
        export_file_path = options['export_file']

        active_sites = get_active_sites()

        with open(export_file_path, mode='w', encoding='utf-8') as export_file:
            for site in active_sites:
                config = site.configuration
                site_values = config.site_values.copy()

                # Pre-prod candidate URLs won't work for production environment.
                if 'SITE_NAME' in site_values:
                    del site_values['SITE_NAME']
                if 'LMS_ROOT_URL' in site_values:
                    del site_values['LMS_ROOT_URL']

                export_json = {
                    'site_id': site.id,
                    'site_values': site_values,
                    'sass_variables': config.sass_variables,
                    'page_elements': config.page_elements,
                }

                # Using the https://jsonlines.org/ format to avoid having too large arrays
                export_file.write(json.dumps(export_json))
                export_file.write('\n')
