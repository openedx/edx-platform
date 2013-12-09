from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    args = ''
    help = 'Checks LinkedIn for students that are on LinkedIn'

    def handle(self, *args, **options):
        print "Hello World!"
