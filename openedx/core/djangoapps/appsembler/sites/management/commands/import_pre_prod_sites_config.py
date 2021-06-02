"""
Used for moving pre-prod candidate configs and theme updates to production after release upgrade.
"""

import json
import traceback

from django.contrib.sites.models import Site
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Import configurations of active sites from pre-production candidate servers in jsonlines.org format.'

    def add_arguments(self, parser):
        parser.add_argument(
            'import_file',
            help='The path of the `.jsonl` file to be imported.',
            type=str,
        )

    def handle(self, *args, **options):
        export_file_path = options['import_file']

        with open(export_file_path, mode='r', encoding='utf-8') as import_file:
            for site_json_line in import_file:
                site_export_json = json.loads(site_json_line)

                site = Site.objects.get(pk=site_export_json['site_id'])
                self.stdout.write('START: Importing the site configs: `{domain}`'.format(domain=site.domain))

                config = site.configuration
                # Updates the values inline to keep SEGMENT_KEY and other values
                config.site_values.update(site_export_json['site_values'])

                # Override `sass_variables` and `page_elements` entirely because merge isn't conceivable
                config.sass_variables = site_export_json['sass_variables']
                config.page_elements = site_export_json['page_elements']
                try:
                    config.save()
                    self.stdout.write('SUCCESS: Imported site configs: `{domain}`'.format(domain=site.domain))
                except Exception as e:
                    self.stdout.write('FAILURE: Error in importing site configs: `{domain}`'.format(domain=site.domain))
                    self.stdout.write(str(e))
                    self.stdout.write(traceback.format_exc())
