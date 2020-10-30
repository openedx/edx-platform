from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from contentstore.views.course import reindex_course_and_check_access
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class Command(BaseCommand):
    help = "Force re-index of elasticsearch for all courses"

    def handle(self, *args, **options):
        if not settings.ROOT_URLCONF == 'cms.urls':
            raise CommandError('this command can only be run from within the CMS')
        all_courses = CourseOverview.get_all_courses()
        amc_admin = User.objects.get(username="amc")

        for c in all_courses:
            try:
                reindex_course_and_check_access(c.id, amc_admin)
            except Exception as e:
                print('Error indexing course')
                print((c.id))
                print(e)
