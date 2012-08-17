#!/usr/bin/python
#
# File:   manage_class_groups
#
# list and edit membership in class staff group

import os, sys, string, re
import datetime
from getpass import getpass
import json
import readline

sys.path.append(os.path.abspath('.'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'lms.envs.dev'

#try:
#    from lms.envs.dev import *
#except Exception as err:
#    print "Run this script from the top-level mitx directory (mitx_all/mitx), not a subdirectory."
#    sys.exit(-1)

from django.conf import settings
from django.contrib.auth.models import User, Group

#-----------------------------------------------------------------------------
# get all staff groups

gset = Group.objects.all()

print "Groups:"
for cnt,g in zip(range(len(gset)), gset):
    print "%d. %s" % (cnt,g)

gnum = int(raw_input('Choose group to manage (enter #): '))

group = gset[gnum]

#-----------------------------------------------------------------------------
# users in group

uall = User.objects.all()
print "----"
print "List of All Users: %s" % [str(x.username) for x in uall]
print "----"

while True:

    print "Users in the group:"
    
    uset = group.user_set.all()
    for cnt, u in zip(range(len(uset)), uset):
        print "%d. %s" % (cnt, u)

    action = raw_input('Choose user to delete (enter #) or enter usernames (comma delim) to add: ')

    m = re.match('^[0-9]+$',action)
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
        
    
    
