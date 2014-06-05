from django.core.management.base import BaseCommand, CommandError

from courseware.courses import get_course


class Command(BaseCommand):
    args = "<course_id>"

    def handle(self, *args, **options):
        if not args:
            raise CommandError("Course id not specified")
        if len(args) > 1:
            raise CommandError("Only one course id may be specifiied")
        course_id = args[0]

        try:
            course = get_course(course_id)
        except ValueError:
            raise CommandError("Invalid course id: {}".format(course_id))

        if course.discussion_link:
            self.stdout.write(course.discussion_link)
