'''
This is a one-off command aimed at fixing a temporary problem encountered where partial credit was awarded for
code problems, but the resulting score (or grade) was mistakenly set to zero because of a bug in
CorrectMap.get_npoints().
'''

import json
import logging
from optparse import make_option

from django.core.management.base import BaseCommand

from courseware.models import StudentModule
from capa.correctmap import CorrectMap

LOG = logging.getLogger(__name__)


class Command(BaseCommand):
    '''
    The fix here is to recalculate the score/grade based on the partial credit.
    To narrow down the set of problems that might need fixing, the StudentModule
    objects to be checked is filtered down to those:

        created < '2013-03-08 15:45:00' (the problem must have been answered before the fix was installed,
                                         on Prod and Edge)
        modified > '2013-03-07 20:18:00' (the problem must have been visited after the bug was introduced)
        state like '%"npoints": 0.%' (the problem must have some form of partial credit).
    '''

    num_visited = 0
    num_changed = 0

    option_list = BaseCommand.option_list + (
        make_option('--save',
                    action='store_true',
                    dest='save_changes',
                    default=False,
                    help='Persist the changes that were encountered.  If not set, no changes are saved.'), )

    def fix_studentmodules(self, save_changes):
        '''Identify the list of StudentModule objects that might need fixing, and then fix each one'''
        modules = StudentModule.objects.filter(modified__gt='2013-03-07 20:18:00',
                                               created__lt='2013-03-08 15:45:00',
                                               state__contains='"npoints": 0.')

        for module in modules:
            self.fix_studentmodule_grade(module, save_changes)

    def fix_studentmodule_grade(self, module, save_changes):
        ''' Fix the grade assigned to a StudentModule'''
        module_state = module.state
        if module_state is None:
            # not likely, since we filter on it.  But in general...
            LOG.info(
                u"No state found for %s module %s for student %s in course %s",
                module.module_type,
                module.module_state_key,
                module.student.username,
                module.course_id,
            )
            return

        state_dict = json.loads(module_state)
        self.num_visited += 1

        # LoncapaProblem.get_score() checks student_answers -- if there are none, we will return a grade of 0
        # Check that this is the case, but do so sooner, before we do any of the other grading work.
        student_answers = state_dict['student_answers']
        if (not student_answers) or len(student_answers) == 0:
            # we should not have a grade here:
            if module.grade != 0:
                log_msg = (
                    u"No answer found but grade %(grade)s exists for %(type)s module %(id)s for student %(student)s " +
                    u"in course %(course_id)s"
                )

                LOG.error(log_msg, {
                    "grade": module.grade,
                    "type": module.module_type,
                    "id": module.module_state_key,
                    "student": module.student.username,
                    "course_id": module.course_id,
                })
            else:
                log_msg = (
                    u"No answer and no grade found for %(type)s module %(id)s for student %(student)s " +
                    u"in course %(course_id)s"
                )

                LOG.debug(log_msg, {
                    "grade": module.grade,
                    "type": module.module_type,
                    "id": module.module_state_key,
                    "student": module.student.username,
                    "course_id": module.course_id,
                })
            return

        # load into a CorrectMap, as done in LoncapaProblem.__init__():
        correct_map = CorrectMap()
        if 'correct_map' in state_dict:
            correct_map.set_dict(state_dict['correct_map'])

        # calculate score the way LoncapaProblem.get_score() works, by deferring to
        # CorrectMap's get_npoints implementation.
        correct = 0
        for key in correct_map:
            correct += correct_map.get_npoints(key)

        if module.grade == correct:
            # nothing to change
            log_msg = u"Grade matches for %(type)s module %(id)s for student %(student)s in course %(course_id)s"
            LOG.debug(log_msg, {
                "type": module.module_type,
                "id": module.module_state_key,
                "student": module.student.username,
                "course_id": module.course_id,
            })
        elif save_changes:
            # make the change
            log_msg = (
                u"Grade changing from %(grade)s to %(correct)s for %(type)s module " +
                u"%(id)s for student %(student)s in course %(course_id)s"
            )

            LOG.debug(log_msg, {
                "grade": module.grade,
                "correct": correct,
                "type": module.module_type,
                "id": module.module_state_key,
                "student": module.student.username,
                "course_id": module.course_id,
            })

            module.grade = correct
            module.save()
            self.num_changed += 1
        else:
            # don't make the change, but log that the change would be made
            log_msg = (
                u"Grade would change from %(grade)s to %(correct)s for %(type)s module %(id)s for student " +
                u"%(student)s in course %(course_id)s"
            )

            LOG.debug(log_msg, {
                "grade": module.grade,
                "correct": correct,
                "type": module.module_type,
                "id": module.module_state_key,
                "student": module.student.username,
                "course_id": module.course_id,
            })

            self.num_changed += 1

    def handle(self, **options):
        '''Handle management command request'''

        save_changes = options['save_changes']

        LOG.info("Starting run: save_changes = {0}".format(save_changes))

        self.fix_studentmodules(save_changes)

        LOG.info("Finished run:  updating {0} of {1} modules".format(self.num_changed, self.num_visited))
