from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site

from cms.djangoapps.course_creators.models import CourseCreator
from organizations.models import Organization
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from student.roles import CourseAccessRole


class Command(BaseCommand):
    help = "Deletes all user, organization and microsite data." \
           " Keeps the superusers and the default site"

    def handle(self, *args, **options):
        # delete course creator permissions
        CourseCreator.objects.all().delete()
        CourseAccessRole.objects.all().delete()

        # remove organizations and users
        for org in Organization.objects.all():
            org.users.all().delete()
            org.delete()

        # remove sites and site configurations
        for site in Site.objects.exclude(id=settings.SITE_ID):
            try:
                site.configuration.delete()
            except SiteConfiguration.DoesNotExist:
                pass
            site.delete()

        # remove any leftover users that weren't a part of a organization
        User.objects.exclude(is_superuser=True).delete()
