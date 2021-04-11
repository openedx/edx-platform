from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from openedx.core.djangoapps.django_comment_common.models import Role


class Command(BaseCommand):
    help = 'Assign a discussion forum role to a user.'

    def add_arguments(self, parser):
        parser.add_argument('name_or_email',
                            help='username or email address of the user to assign a role')
        parser.add_argument('role',
                            help='the role to which the user will be assigned')
        parser.add_argument('course_id',
                            help='the edx course_id')
        parser.add_argument('--remove',
                            action='store_true',
                            help='remove the role instead of adding/assigning it')

    def handle(self, *args, **options):
        name_or_email = options['name_or_email']
        role = options['role']
        course_id = options['course_id']

        role = Role.objects.get(name=role, course_id=course_id)

        if '@' in name_or_email:
            user = User.objects.get(email=name_or_email)
        else:
            user = User.objects.get(username=name_or_email)

        if options['remove']:
            user.roles.remove(role)
        else:
            user.roles.add(role)

        print('Success!')
