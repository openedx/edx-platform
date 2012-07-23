from django.utils.simplejson import dumps
from django.core.management.base import BaseCommand, CommandError
from certificates.models import GeneratedCertificate


class Command(BaseCommand):

    help = """
    This command finds all GeneratedCertificate objects that do not have a
    certificate generated. These come into being when a user requests a
    certificate, or when grade_all_students is called (for pre-generating
    certificates).

    It returns a json formatted list of users and their user ids
    """

    def handle(self, *args, **options):
        users = GeneratedCertificate.objects.filter(
                download_url=None)
        user_output = [{'user_id':user.user_id, 'name':user.name}
                for user in users]
        self.stdout.write(dumps(user_output) + "\n")
