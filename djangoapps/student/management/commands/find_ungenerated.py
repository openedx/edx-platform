from django.utils.simplejson import dumps
from django.core.management.base import BaseCommand, CommandError
from certificates.models import GeneratedCertificate
class Command(BaseCommand):
    def handle(self, *args, **options):
        users = GeneratedCertificate.objects.filter(
                download_url = None )
        user_output = [{'user_id':user.user_id, 'name':user.name}
                for user in users]
        self.stdout.write(dumps(user_output) + "\n")
