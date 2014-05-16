#!/usr/bin/python
#
# 19-Sep-13 ichuang@mit.edu

import csv
from courseware.module_tree_reset import *
from django.core.management.base import BaseCommand

#-----------------------------------------------------------------------------

from django.conf import settings
from xmodule.modulestore.django import modulestore
from django.dispatch import Signal
from request_cache.middleware import RequestCache

from django.core.cache import get_cache

if True:
    CACHE = get_cache('mongo_metadata_inheritance')
    for store_name in settings.MODULESTORE:
        store = modulestore(store_name)
        store.metadata_inheritance_cache_subsystem = CACHE
        store.request_cache = RequestCache.get_request_cache()

        modulestore_update_signal = Signal(providing_args=['modulestore', 'course_id', 'location'])
        store.modulestore_update_signal = modulestore_update_signal

#-----------------------------------------------------------------------------

class Command(BaseCommand):
    help = """Reset exam attempts for 3.091 exam, Fall 2013.
Records students and problems which were reset.
Give filename as argument.  Output is CSV file."""

    def handle(self, *args, **options):
        # fn = 'reset_3091exam.csv'
        fn = args[0]

        pminfo = ProctorModuleInfo()

        students = User.objects.filter(courseenrollment__course_id=pminfo.course.id).order_by('username')
        # students = User.objects.filter(username='ichuang')

        data = []

        # write out to csv file

        fieldnames = ['id', 'name', 'username', 'assignment', 'problem', 'date', 'earned', 'possible']
        fp = open(fn,'w')
        csvf = csv.DictWriter(fp, fieldnames, dialect="excel", quotechar='"', quoting=csv.QUOTE_ALL)
        csvf.writeheader()

        cnt = 0
        for student in students:
            dat = pminfo.get_assignments_attempted_and_failed(student, do_reset=True)
            data += dat
            for row in dat:
                csvf.writerow(row)
            fp.flush()
            cnt += 1
            #if cnt>3:
            #    break
        fp.close()

        # print data
