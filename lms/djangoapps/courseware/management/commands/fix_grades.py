import json
import itertools

from pprint import pprint

from django.db.models import F
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError, make_option

from courseware.grades import iterate_grades_for
from courseware.models import StudentModule, StudentModuleHistory
from courseware.module_tree_reset import ProctorModuleInfo

from xmodule.modulestore import Location


class Command(BaseCommand):
    args = "<course_id>"
    help = """Show and optionally fix any lost grades for 3.091r"""
    option_list = BaseCommand.option_list + (
        make_option('--fix-it-for-real-i-mean-it',
                    dest='fix_it_for_real_i_mean_it',
                    action='store_true',
                    default=False,
                    help='Restore lost grades'),
    )

    def get_lost_grades(self):
        grades = list(iterate_grades_for(self.pmi.course.id, User.objects.all()))

        history_entries = StudentModuleHistory.objects.filter(
            # test if results are same without these three Q's
            # (seems to be the case)
            #Q(state__contains='"attempts"') &
            #Q(state__contains='"correct_map"') &
            #Q(state__contains='"student_answers"'),
            grade__isnull=False, max_grade__isnull=False,
            grade=F("max_grade"),
        )

        lost_grades = {}

        for user, gradeset, err_msg in grades:
            if err_msg:
                print "!!! GRADING FAILURE FOR USER '%s': %s" % (user, err_msg)
                continue
            entries = history_entries.filter(student_module__student=user)
            _scores = gradeset['totaled_scores'].values()
            total_scores = dict([(i.section, i) for i in
                                 itertools.chain.from_iterable(_scores)])
            for e in entries:
                loc = Location(e.student_module.module_state_key)
                sec_name = loc.name.split(':')[1]
                score = total_scores.get(sec_name)
                if score is None:
                    continue
                if score.earned != score.possible:
                    if e.grade != e.max_grade:
                        raise Exception("e.grade = %s != e.max_grade = %s" %
                                        (e.grade, e.max_grade))
                    lost = lost_grades.get(user.username, {})
                    lost[sec_name] = [score.earned, score.possible, e.grade,
                                      e.max_grade, e]
                    lost_grades[user.username] = lost

        return lost_grades

    def fix_grades(self, lost_grades):
        for user in lost_grades:
            lost_dict = lost_grades.get(user)
            rpmod_dict = dict([(i.location.name, i) for i in self.pmi.rpmods])
            for section in lost_dict:
                lost = lost_dict.get(section)
                pmod = rpmod_dict.get(section)
                rloc = pmod.get_children()[0].get_children()[0].location.url()
                rsm = StudentModule.objects.get(student__username=user,
                                               module_state_key=rloc)
                state = json.loads(rsm.state)
                history = state.get('history', []) or []
                successful_submission = lost[-1]
                sm = lost[-1].student_module
                choice = sm.module_state_key
                if choice not in history:
                    history.append(choice)
                state['choice'] = choice
                state['history'] = history
                rsm.state = json.dumps(state)
                rsm.save()
                if sm.grade != successful_submission.grade:
                    sm.grade = successful_submission.grade
                    sm.state = successful_submission.state
                    sm.save()

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("insufficient arguments")
        self.pmi = ProctorModuleInfo(args[0])
        lost_grades = self.get_lost_grades()
        total = sum([len(i.keys()) for i in lost_grades.values()])
        pprint(lost_grades)
        print 'Total: %s' % total
        fix_it_for_real_i_mean_it = options.get('fix_it_for_real_i_mean_it')
        if fix_it_for_real_i_mean_it:
            print '!!! Fixing grades now...'
            self.fix_grades(lost_grades)
