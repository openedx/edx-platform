from django.core.management.base import BaseCommand, CommandError
from django.contrib.sites.models import Site
from django.db import transaction


class Command(BaseCommand):
    """
    Disable a custom domain

    Also requires running `disable_custom_domain` on AMC
    """

    def add_arguments(self, parser):
        parser.add_argument(
            'domain',
            help='The custom domain disabled.',
            type=str,
        )

    @transaction.atomic
    def handle(self, *args, **options):
        domain = options['domain']
        try:
            # find the site that matches the custom domain to disable
            s = Site.objects.get(domain=domain)

            # update it's corresponding Site
            ad = s.alternative_domain
            s.domain = ad.domain
            s.save()

            # then remove the AlternativeDomain
            ad.delete()
        except Site.DoesNotExist:
            raise CommandError('Cannot find custom domain "%s"' % domain)
