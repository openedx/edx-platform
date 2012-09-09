#!/usr/bin/python
#
# generate pyschometrics data from tracking logs and student module data

import os, sys, string
import datetime
import json

from courseware.models import *
from track.models import *
from psychometrics.models import *
from xmodule.modulestore import Location

from django.core.management.base import BaseCommand

#db = "ocwtutor"	# for debugging
db = "default"

class Command(BaseCommand):
    help = "initialize PsychometricData tables from StudentModule instances (and tracking data, if in SQL)."
    help += "Note this is done for all courses for which StudentModule instances exist."

    def handle(self, *args, **options):

        # delete all pmd

        #PsychometricData.objects.all().delete()
        #PsychometricData.objects.using(db).all().delete()

        smset = StudentModule.objects.using(db).exclude(max_grade=None)
        
        for sm in smset:
            url = sm.module_state_key
            location = Location(url)
            if not location.category=="problem":
                continue
            try:
                state = json.loads(sm.state)
                done = state['done']
            except:
                print "Oops, failed to eval state for %s (state=%s)" % (sm,sm.state)
                continue
            
            if done:			# only keep if problem completed
                try:
                    pmd = PsychometricData.objects.using(db).get(studentmodule=sm)
                except PsychometricData.DoesNotExist:
                    pmd = PsychometricData(studentmodule=sm)
        
                pmd.done = done
                pmd.attempts = state['attempts']
        
                # get attempt times from tracking log
                uname = sm.student.username
                tset = TrackingLog.objects.using(db).filter(username=uname, event_type__contains='save_problem_check')        
                tset = tset.filter(event_source='server')
                tset = tset.filter(event__contains="'%s'" % url)
                checktimes = [x.dtcreated for x in tset]
                pmd.checktimes = json.dumps(checktimes)
                if not len(checktimes)==pmd.attempts:
                    print "Oops, mismatch in number of attempts and check times for %s" % pmd
        
                #print pmd
                pmd.save(using=db)
        
        print "%d PMD entries" % PsychometricData.objects.using(db).all().count()
