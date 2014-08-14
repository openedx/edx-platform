import json

from django.core.management.base import BaseCommand, CommandError, make_option

from courseware.module_tree_reset import ProctorModuleInfo


class Command(BaseCommand):
    args = "<course_id> <username>"
    help = """Show submission history for student in course (3.091r)"""
    option_list = BaseCommand.option_list + (
        make_option('--csv-output-filename',
                    dest='csv_output_filename',
                    action='store',
                    default=None,
                    help='Save stats to csv file'),
    )

    def handle(self, *args, **options):
        if len(args) != 2:
            raise CommandError("insufficient arguments")

        course_id, username = args

        lev1 = '-' * 4 + '>'
        lev2 = '-' * 8 + '>'
        div = '*' * 50

        pminfo = ProctorModuleInfo(course_id)

        problem_banks = {}
        for rpmod in pminfo.rpmods:
            bank = problem_banks[rpmod.procset_name] = []
            #assignment_set_name = rpmod.ra_ps.display_name
            for ploc in rpmod.ra_rand.children:
                problem = pminfo.ms.get_instance(pminfo.course.id, ploc)
                #problem.assignment_set_name = assignment_set_name
                bank.append(problem.location.url())

        submission_history = [
            (bank, pminfo.submission_history(username, problem_banks.get(bank)))
            for bank in problem_banks]

        skip_blank = True
        if skip_blank:
            submission_history = [(i, j) for i, j in submission_history if
                                  len(j['history_entries']) > 0]

        for bank, entries in submission_history:
            print lev1, bank
            for smh in entries['history_entries']:
                state = json.loads(smh.state)
                print lev2, div
                print lev2, 'Location: %s' % smh.student_module.module_state_key
                print lev2, 'Score: %s/%s' % (smh.grade, smh.max_grade)
                print lev2, 'Attempts: %s' % state['attempts']
                print lev2, 'Answers: %s' % state['student_answers']
                #print lev2, 'State: %s' % state
