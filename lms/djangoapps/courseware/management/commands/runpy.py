from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    args = "<script>"
    help = "Run a Python script within the edx platform lms environment"

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("missing script argument")
        script = args[0]
        return execfile(script)
