#!/usr/bin/python
#
# Largely for 3.091-exam.
#
# Compute number of times a given problem has been attempted by a student, including StudentModuleHistory.
# Do this by walking through the course tree.  For every assessment problem, look up all matching
# StudehtModuleHistory items.  Count number of attempts passed, and number failed.  Remove staff data.
#
# Output table with: problem url_id, problem name, number students assigned, number attempts failed, number attempts succeeded
#

from courseware.module_tree_reset import *
from courseware.access import get_access_group_name
from django.core.management.base import BaseCommand
import json
import csv

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

def ComputeStats():
    pminfo = ProctorModuleInfo()

    # get list of all problems

    all_problems = []
    stats = []

    self = pminfo

    if True:
        for rpmod in self.rpmods:
            assignment_set_name = rpmod.ra_ps.display_name
            for ploc in rpmod.ra_rand.children:
                problem = self.ms.get_item(ploc)
                problem.assignment_set_name = assignment_set_name
                all_problems.append(problem)

    staffgroup = get_access_group_name(self.course, 'staff')
    cnt = 0

    class Stats(object):
        def __init__(self):
            self.nassigned = 0
            self.nattempts = 0
            self.npassed = 0

    for problem in all_problems:
        print problem.id

        stat = Stats()

        smset0 = StudentModule.objects.filter(module_state_key=problem.id, student__is_staff=False)
        smset = smset0.exclude(student__groups__name=staffgroup)

        def passed(state):
            if 'correct_map' not in state:
                return False
            if not state['correct_map']:	# correct_map = {}
                return False
            return all([x['correctness']=='correct' for x in state.get('correct_map').values()])	# must be all correct to pass

        def update_stats(sm, stat, history=False):
            if sm.grade is None:
                return
            state = json.loads(sm.state)
            if not 'attempts' in state:
                return
            if not state.get('done', False):
                return "notdone"
            if not history:
                stat.nattempts += state['attempts']
            if passed(state):
                stat.npassed += 1
                return "passed"
            return "attempted"

        for sm in smset:
            stat.nassigned += 1
            ret = update_stats(sm, stat)
            if ret in ['passed', 'attempted']:
                continue

            smhset = StudentModuleHistory.objects.filter(student_module=sm)
            states = [ json.loads(smh.state) for smh in smhset ]
            okset = [ passed(x) for x in states ]
            attempts = [ x.get('attempts', 0) for x in states]

            stat.nattempts += max(attempts)
            if any(okset):
                stat.npassed += 1

        #print "    assigned=%d, attempts=%d, passed=%d" % (nassigned, nattempts, npassed)
        stats.append(dict(problem_id=problem.id,
                          pset=problem.assignment_set_name,
                          problem_name=problem.display_name,
                          due=str(problem.due),
                          max_attempts=problem.max_attempts,
                          assigned=stat.nassigned,
                          attempts=stat.nattempts,
                          passed=stat.npassed,
                          ))
        cnt += 1

        #if cnt>5:
        #    break

    if True:
        dddir = settings.MITX_FEATURES.get('DOWNLOAD_DATA_DIR','')
        fndir = dddir / (self.course.id.replace('/','__'))
        dt = datetime.datetime.now().strftime('%Y-%m-%d-%H%M')
        fn = fndir / "problem-stats-%s-%s.csv" % (self.course.id.split('/')[1], dt)

        print "Saving data to %s" % fn
        # fn = "stats.csv"

        fieldnames = ['problem_id', 'pset', 'problem_name', 'due', 'max_attempts', 'assigned', 'attempts', 'passed']
        fp = open(fn,'w')
        writer = csv.DictWriter(fp, fieldnames, dialect='excel', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for row in stats:
            try:
                writer.writerow(row)
            except Exception as err:
                print "Oops, failed to write %s, error=%s" % (row, err)
        fp.close()

#-----------------------------------------------------------------------------


class Command(BaseCommand):
    help = """Generate CSV file with problem attempts statistics;
    CSV file columns include problem id, assigned, max_attempts, attempts, passed
    for every problem in the course.  Arguments: None.  Works only on 3.091-exam"""

    def handle(self, *args, **options):
        ComputeStats()
