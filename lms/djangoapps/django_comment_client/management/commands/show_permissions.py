from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User


class Command(BaseCommand):
    args = 'user'
    help = "Show a user's roles and permissions"

    def handle(self, *args, **options):
        print args
        if len(args) != 1:
            raise CommandError("The number of arguments does not match. ")
        try:
            if '@' in args[0]:
                user = User.objects.get(email=args[0])
            else:
                user = User.objects.get(username=args[0])
        except User.DoesNotExist:
            print "User %s does not exist. " % args[0]
            print "Available users: "
            print User.objects.all()
            return

        roles = user.roles.all()
        print "%s has %d roles:" % (user, len(roles))
        for role in roles:
            print "\t%s" % role

        for role in roles:
            print "%s has permissions: " % role
            print role.permissions.all()
