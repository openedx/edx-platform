from django.conf import settings
from django.core.management.base import NoArgsCommand

from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from openedx.core.djangoapps.appsembler.sites.utils import to_new_page_elements


class Command(NoArgsCommand):
    help = 'Use the language aware page elements JSON structure for all sites.'

    def handle(self, **options):
        for site_configs in SiteConfiguration.objects.exclude(site__id=settings.SITE_ID):
            current_page = site_configs.page_elements
            to_new_page_elements(current_page)
            site_configs.page_elements = current_page

            site_configs.site_values['LANGUAGE_CODE'] = site_configs.site_values.get(
                'LANGUAGE_CODE', site_configs.site_values.get(
                    'site_default_language', 'en'
                )
            )

            if 'site_default_language' in site_configs.site_values:
                del site_configs.site_values['site_default_language']

            site_configs.site_values['site_enabled_languages'] = site_configs.site_values.get(
                'site_enabled_languages', [
                    {
                        'languageCode': 'en',
                        'isDefault': True,
                        'languageName': 'English',
                    },
                ]
            )

            site_configs.save()
