from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django_comment_common.models import Role
from django.contrib.auth.models import User


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--remove',
                    action='store_true',
                    dest='remove',
                    default=False,
                    help='Remove the role instead of adding it'),
    )

    args = '<user|email> <role> <course_id>'
    help = 'Assign a discussion forum role to a user '

    def handle(self, *args, **options):
        if len(args) != 3:
            raise CommandError('Usage is assign_role {0}'.format(self.args))

        name_or_email, role, course_id = args

        role = Role.objects.get(name=role, course_id=course_id)

        if '@' in name_or_email:
            user = User.objects.get(email=name_or_email)
        else:
            user = User.objects.get(username=name_or_email)

        if options['remove']:
            user.roles.remove(role)
        else:
            user.roles.add(role)

        print 'Success!'
