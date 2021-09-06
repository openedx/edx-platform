from django.core.management import BaseCommand, CommandError

from openedx.core.djangoapps.appsembler.sites.utils import get_active_sites


class Command(BaseCommand):
    help = "DANGEROUS: Renames all domains for production/staging candidate. Remove Google Tag Manager and Segment keys. Do not run during on production!"

    def add_arguments(self, parser):
        parser.add_argument(
            'from',
            help='The production/staging domain e.g. "tahoe.appsembler.com"',
            type=str,
        )

        parser.add_argument(
            'to',
            help='The candidate domain e.g. "tahoe-us-juniper-prod.appsembler.com"',
            type=str,
        )

    def handle(self, *args, **options):
        sites_with_configs = get_active_sites().filter(configuration__isnull=False)

        has_errors = False
        for site in sites_with_configs:
            self.stdout.write('FROM {}'.format(site.domain))
            site.domain = site.domain.replace('.{}'.format(options['from']), '.{}'.format(options['to']))
            self.stdout.write('TO {}'.format(site.domain))
            site.save()

            site.configuration.site_values['SITE_NAME'] = site.domain

            try:
                del site.configuration.site_values['SEGMENT_KEY']
                self.stdout.write('deleted SEGMENT_KEY')
            except KeyError:
                self.stdout.write('no SEGMENT_KEY')
                pass

            try:
                del site.configuration.site_values['customer_gtm_id']
                self.stdout.write('deleted customer_gtm_id')
            except KeyError:
                self.stdout.write('no customer_gtm_id')
                pass
            try:
                site.configuration.save()
            except Exception as e:
                has_errors = True
                self.stdout.write(e)
            self.stdout.write('---')

        if has_errors:
            msg = 'Some sites have failed, please review this command output for more information.'
            self.stdout.write(msg)
            raise CommandError(msg)
