#!/usr/bin/python
#
# File:   manage_course_groups
#
# interactively list and edit membership in course staff and instructor groups

import re

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

#-----------------------------------------------------------------------------
# get all staff groups


class Command(BaseCommand):
    help = "Manage course group membership, interactively."

    def handle(self, *args, **options):

        gset = Group.objects.all()

        print "Groups:"
        for cnt, g in zip(range(len(gset)), gset):
            print "%d. %s" % (cnt, g)

        gnum = int(raw_input('Choose group to manage (enter #): '))

        group = gset[gnum]

        #-----------------------------------------------------------------------------
        # users in group

        uall = User.objects.all()
        if uall.count() < 50:
            print "----"
            print "List of All Users: %s" % [str(x.username) for x in uall]
            print "----"
        else:
            print "----"
            print "There are %d users, which is too many to list" % uall.count()
            print "----"

        while True:

            print "Users in the group:"

            uset = group.user_set.all()
            for cnt, u in zip(range(len(uset)), uset):
                print "%d. %s" % (cnt, u)

            action = raw_input('Choose user to delete (enter #) or enter usernames (comma delim) to add: ')

            m = re.match('^[0-9]+$', action)
            if m:
                unum = int(action)
                u = uset[unum]
                print "Deleting user %s" % u
                u.groups.remove(group)

            else:
                for uname in action.split(','):
                    try:
                        user = User.objects.get(username=action)
                    except Exception as err:
                        print "Error %s" % err
                        continue
                    print "adding %s to group %s" % (user, group)
                    user.groups.add(group)
