import sys

from django.core.management.base import BaseCommand, CommandError
from certificates.models import GeneratedCertificate
import simplejson
class Command(BaseCommand):
    def handle(self, *args, **options):
        l = GeneratedCertificate.objects.filter( download_url = None ).values()
        sl = [{'user_id':x['user_id'], 'name':x['name']} for x in l]
        sys.stdout.write(simplejson.dumps(sl))
