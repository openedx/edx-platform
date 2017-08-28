import json

from django.core.management import BaseCommand
from django.db import connections


class Command(BaseCommand):
    help = "Outputs the list of custom domains that will be used to generate let's encrypt certs"

    def handle(self, *args, **options):
        cursor = connections['tiers'].cursor()
        cursor.execute("SELECT custom_domain FROM organizations_microsite WHERE custom_domain != '';")
        rows = cursor.fetchall()
        domains = [{'domains': row} for row in rows]
        self.stdout.write(json.dumps(domains))
