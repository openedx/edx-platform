#!/usr/bin/python
#
# File:   create_groups.py
#
# Create all staff_* groups for classes in data directory.

import os, sys, string, re

sys.path.append(os.path.abspath('.'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'lms.envs.dev'

try:
    from lms.envs.dev import *
except Exception as err:
    print "Run this script from the top-level mitx directory (mitx_all/mitx), not a subdirectory."
    sys.exit(-1)

from django.conf import settings
from django.contrib.auth.models import User, Group
from path import path

data_dir = settings.DATA_DIR
print "data_dir = %s" % data_dir

for course_dir in os.listdir(data_dir):
    # print course_dir
    if not os.path.isdir(path(data_dir) / course_dir):
        continue
    gname = 'staff_%s' % course_dir
    if Group.objects.filter(name=gname):
        print "group exists for %s" % gname
        continue
    g = Group(name=gname)
    g.save()
    print "created group %s" % gname
