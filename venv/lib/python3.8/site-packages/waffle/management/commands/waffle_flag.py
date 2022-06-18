from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from waffle import get_waffle_flag_model

UserModel = get_user_model()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            'name',
            nargs='?',
            help='The name of the flag.')
        parser.add_argument(
            '-l', '--list',
            action='store_true',
            dest='list_flags',
            default=False,
            help='List existing samples.')
        parser.add_argument(
            '--everyone',
            action='store_true',
            dest='everyone',
            help='Activate flag for all users.')
        parser.add_argument(
            '--deactivate',
            action='store_false',
            dest='everyone',
            help='Deactivate flag for all users.')
        parser.add_argument(
            '--percent', '-p',
            action='store',
            type=int,
            dest='percent',
            help='Roll out the flag for a certain percentage of users. Takes '
                 'a number between 0.0 and 100.0')
        parser.add_argument(
            '--superusers',
            action='store_true',
            dest='superusers',
            default=False,
            help='Turn on the flag for Django superusers.')
        parser.add_argument(
            '--staff',
            action='store_true',
            dest='staff',
            default=False,
            help='Turn on the flag for Django staff.')
        parser.add_argument(
            '--authenticated',
            action='store_true',
            dest='authenticated',
            default=False,
            help='Turn on the flag for logged in users.')
        parser.add_argument(
            '--group', '-g',
            action='append',
            default=list(),
            help='Turn on the flag for listed group names (use flag more '
                 'than once for multiple groups). WARNING: This will remove '
                 'any currently associated groups unless --append is used!')
        parser.add_argument(
            '--user', '-u',
            action='append',
            default=list(),
            help='Turn on the flag for listed usernames (use flag more '
                 'than once for multiple users). WARNING: This will remove '
                 'any currently associated users unless --append is used!')
        parser.add_argument(
            '--append',
            action='store_true',
            dest='append',
            default=False,
            help='Append only mode when adding groups.')
        parser.add_argument(
            '--rollout', '-r',
            action='store_true',
            dest='rollout',
            default=False,
            help='Turn on rollout mode.')
        parser.add_argument(
            '--create',
            action='store_true',
            dest='create',
            default=False,
            help='If the flag doesn\'t exist, create it.')
        parser.set_defaults(everyone=None)

    help = 'Modify a flag.'

    def handle(self, *args, **options):
        if options['list_flags']:
            self.stdout.write('Flags:')
            for flag in get_waffle_flag_model().objects.iterator():
                self.stdout.write('NAME: %s' % flag.name)
                self.stdout.write('SUPERUSERS: %s' % flag.superusers)
                self.stdout.write('EVERYONE: %s' % flag.everyone)
                self.stdout.write('AUTHENTICATED: %s' % flag.authenticated)
                self.stdout.write('PERCENT: %s' % flag.percent)
                self.stdout.write('TESTING: %s' % flag.testing)
                self.stdout.write('ROLLOUT: %s' % flag.rollout)
                self.stdout.write('STAFF: %s' % flag.staff)
                self.stdout.write('GROUPS: %s' % list(
                    flag.groups.values_list('name', flat=True))
                )
                self.stdout.write('USERS: %s' % list(
                    flag.users.values_list(UserModel.USERNAME_FIELD, flat=True))
                                  )
                self.stdout.write('')
            return

        flag_name = options['name']

        if not flag_name:
            raise CommandError('You need to specify a flag name.')

        if options['create']:
            flag, created = get_waffle_flag_model().objects.get_or_create(name=flag_name)
            if created:
                self.stdout.write('Creating flag: %s' % flag_name)
        else:
            try:
                flag = get_waffle_flag_model().objects.get(name=flag_name)
            except get_waffle_flag_model().DoesNotExist:
                raise CommandError('This flag does not exist.')

        # Loop through all options, setting Flag attributes that
        # match (ie. don't want to try setting flag.verbosity)
        for option in options:
            # Group isn't an attribute on the Flag, but a related Many to Many
            # field, so we handle it a bit differently by looking up groups and
            # adding each group to the flag individually
            if option == 'group':
                group_hash = {}
                for group in options['group']:
                    try:
                        group_instance = Group.objects.get(name=group)
                        group_hash[group_instance.name] = group_instance.id
                    except Group.DoesNotExist:
                        raise CommandError('Group %s does not exist' % group)
                # If 'append' was not passed, we clear related groups
                if not options['append']:
                    flag.groups.clear()
                self.stdout.write('Setting group(s): %s' % (
                    [name for name, _id in group_hash.items()])
                )
                for group_name, group_id in group_hash.items():
                    flag.groups.add(group_id)
            elif option == 'user':
                user_hash = set()
                for username in options['user']:
                    try:
                        user_instance = UserModel.objects.get(
                            Q(**{UserModel.USERNAME_FIELD: username}) |
                            Q(**{UserModel.EMAIL_FIELD: username})
                        )
                        user_hash.add(user_instance)
                    except UserModel.DoesNotExist:
                        raise CommandError('User %s does not exist' % username)
                # If 'append' was not passed, we clear related users
                if not options['append']:
                    flag.users.clear()
                self.stdout.write('Setting user(s): %s' % user_hash)
                # for user in user_hash:
                flag.users.add(*[user.id for user in user_hash])
            elif hasattr(flag, option):
                self.stdout.write('Setting %s: %s' % (option, options[option]))
                setattr(flag, option, options[option])

        flag.save()
