from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--list',
                    action='store_true',
                    dest='list',
                    default=False,
                    help='List available groups'),
        make_option('--create',
                    action='store_true',
                    dest='create',
                    default=False,
                    help='Create the group if it does not exist'),
        make_option('--remove',
                    action='store_true',
                    dest='remove',
                    default=False,
                    help='Remove the user from the group instead of adding it'),
        )

    args = '<user|email> <group>'
    help = 'Add a user to a group'

    def print_groups(self):
        print 'Groups available:'
        for group in Group.objects.all().distinct():
            print '  ', group.name

    def handle(self, *args, **options):
        if options['list']:
            self.print_groups()
            return

        if len(args) != 2:
            raise CommandError('Usage is add_to_group {0}'.format(self.args))

        name_or_email, group_name = args

        if '@' in name_or_email:
            user = User.objects.get(email=name_or_email)
        else:
            user = User.objects.get(username=name_or_email)

        try:
            group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            if options['create']:
                group = Group(name=group_name)
                group.save()
            else:
                raise CommandError('Group {} does not exist'.format(group_name))

        if options['remove']:
            user.groups.remove(group)
        else:
            user.groups.add(group)

        print 'Success!'
