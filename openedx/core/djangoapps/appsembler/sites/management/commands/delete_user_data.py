from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.contrib.sites.models import Site

from cms.djangoapps.course_creators.models import CourseCreator
from organizations.models import Organization
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from student.roles import CourseAccessRole


class Command(BaseCommand):
    help = "Deletes a user (or multiple), their organization and all users and their microsite data."

    def add_arguments(self, parser):
        parser.add_argument('email', nargs='*')

    def handle(self, *args, **options):
        for email in options['email']:
            try:
                user = User.objects.get(email=email)
            except:
                print('User "{0}" does not exist'.format(email))
                return

            # delete course creator permissions
            CourseCreator.objects.filter(user=user).delete()
            CourseAccessRole.objects.filter(user=user).delete()

            # remove organizations and microsites
            for org in user.organizations.all():
                try:
                    site = Site.objects.get(name=org.name)
                    site.delete()
                except Site.DoesNotExist:
                    pass
                org.delete()

            # finally, delete the user
            user.delete()
