#!/usr/bin/python
#
# File:   create_groups.py
#
# Create all staff_* groups for classes in data directory.

import os

from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import Group
from path import Path as path
from lxml import etree


def create_groups():
    '''
    Create staff and instructor groups for all classes in the data_dir
    '''

    data_dir = settings.DATA_DIR
    print "data_dir = %s" % data_dir

    for course_dir in os.listdir(data_dir):

        if course_dir.startswith('.'):
            continue
        if not os.path.isdir(path(data_dir) / course_dir):
            continue

        cxfn = path(data_dir) / course_dir / 'course.xml'
        try:
            coursexml = etree.parse(cxfn)
        except Exception:  # pylint: disable=broad-except
            print "Oops, cannot read %s, skipping" % cxfn
            continue
        cxmlroot = coursexml.getroot()
        course = cxmlroot.get('course')		# TODO (vshnayder!!): read metadata from policy file(s) instead of from course.xml
        if course is None:
            print "oops, can't get course id for %s" % course_dir
            continue
        print "course=%s for course_dir=%s" % (course, course_dir)

        create_group('staff_%s' % course)		# staff group
        create_group('instructor_%s' % course)		# instructor group (can manage staff group list)


def create_group(gname):
    if Group.objects.filter(name=gname):
        print "    group exists for %s" % gname
        return
    g = Group(name=gname)
    g.save()
    print "    created group %s" % gname


class Command(BaseCommand):
    help = "Create groups associated with all courses in data_dir."

    def handle(self, *args, **options):
        create_groups()
