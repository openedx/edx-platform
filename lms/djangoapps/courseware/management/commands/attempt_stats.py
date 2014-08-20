#!/usr/bin/python
#
# Compute number of times a given problem has been attempted by a student,
# including StudentModuleHistory.  Do this by walking through the course tree.
# For every assessment problem, look up all matching StudehtModuleHistory
# items.  Count number of attempts passed, and number failed.  Remove staff
# data.
#
# Output table with: problem url_id, problem name, number students assigned,
# number attempts failed, number attempts succeeded
#
import csv
import json

from django.core.management.base import BaseCommand, CommandError, make_option

from student import roles
from courseware.module_tree_reset import ProctorModuleInfo
from courseware.models import StudentModule, StudentModuleHistory


class Stats(object):
    def __init__(self):
        self.nassigned = 0
        self.nattempts = 0
        self.npassed = 0


def passed(state):
    if 'correct_map' not in state:
        return False
    if not state['correct_map']:
        return False
    # must all be correct to pass
    return all([x['correctness'] == 'correct' for x in
                state.get('correct_map').values()])


def update_stats(sm, stat, history=False):
    if sm.grade is None:
        return
    state = json.loads(sm.state or '{}')
    if 'attempts' not in state:
        return
    if not state.get('done', False):
        return "notdone"
    if not history:
        stat.nattempts += state['attempts']
    if passed(state):
        stat.npassed += 1
        return "passed"
    return "attempted"


def compute_stats(course_id):
    pminfo = ProctorModuleInfo(course_id)
    all_problems = []
    stats = []
    course_url = pminfo.course.location.url()
    staff_role = roles.CourseStaffRole(course_url)
    inst_role = roles.CourseInstructorRole(course_url)
    exclude_groups = staff_role._group_names + inst_role._group_names

    for rpmod in pminfo.rpmods:
        assignment_set_name = rpmod.ra_ps.display_name
        for ploc in rpmod.ra_rand.children:
            problem = pminfo.ms.get_instance(pminfo.course.id, ploc)
            problem.assignment_set_name = assignment_set_name
            all_problems.append(problem)

    for problem in all_problems:
        stat = Stats()
        smset = StudentModule.objects.filter(
            module_state_key=problem.id, student__is_staff=False
        ).exclude(student__groups__name__in=exclude_groups)
        for sm in smset:
            stat.nassigned += 1
            ret = update_stats(sm, stat)
            if ret in ['passed', 'attempted']:
                continue
            smhset = StudentModuleHistory.objects.filter(student_module=sm)
            states = [json.loads(smh.state or '{}') for smh in smhset]
            okset = [passed(x) for x in states]
            attempts = [x.get('attempts', 0) for x in states]
            stat.nattempts += max(attempts)
            if any(okset):
                stat.npassed += 1

        print problem.id
        print "    assigned=%d, attempts=%d, passed=%d" % (
            stat.nassigned, stat.nattempts, stat.npassed)
        stats.append(dict(
            problem_id=problem.id,
            pset=problem.assignment_set_name,
            problem_name=problem.display_name,
            due=str(problem.due),
            max_attempts=problem.max_attempts,
            assigned=stat.nassigned,
            attempts=stat.nattempts,
            passed=stat.npassed,
        ))
    return stats


def write_stats(stats, csv_filename):
    print "Saving data to %s" % csv_filename
    fieldnames = ['problem_id', 'pset', 'problem_name', 'due', 'max_attempts',
                  'assigned', 'attempts', 'passed']
    fp = open(csv_filename, 'w')
    writer = csv.DictWriter(fp, fieldnames, dialect='excel', quotechar='"',
                            quoting=csv.QUOTE_ALL)
    writer.writeheader()
    for row in stats:
        try:
            writer.writerow(row)
        except Exception as err:
            print "Oops, failed to write %s, error=%s" % (row, err)
    fp.close()
    return


class Command(BaseCommand):
    args = "<course_id>"
    help = """Generate CSV file with problem attempts statistics; CSV file \
columns include problem id, assigned, max_attempts, attempts, passed for \
every problem in the course.  Arguments: None.  Works only on 3.091-exam"""
    option_list = BaseCommand.option_list + (
        make_option('--csv-output-filename',
                    dest='csv_output_filename',
                    action='store',
                    default=None,
                    help='Save stats to csv file'),
    )

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("missing argument: <course_id>")
        stats = compute_stats(args[0])
        csv_output_filename = options['csv_output_filename']
        if csv_output_filename:
            write_stats(stats, csv_output_filename)
