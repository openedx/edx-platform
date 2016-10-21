from django.core.management.base import NoArgsCommand

from appsembler.models import update_course_statistics, update_user_statistics


class Command(NoArgsCommand):
    help = '''Sends statistics to Intercom'''

    def handle(self, **options):
        update_course_statistics(verbose=True)
        update_user_statistics(verbose=True)