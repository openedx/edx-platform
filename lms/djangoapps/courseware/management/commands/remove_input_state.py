'''
This is a one-off command aimed at fixing a temporary problem encountered where input_state was added to
the same dict object in capa problems, so was accumulating.  The fix is simply to remove input_state entry
from state for all problems in the affected date range.
'''

import json
import logging
from optparse import make_option

from django.core.management.base import BaseCommand
from django.db import transaction

from courseware.models import StudentModule, StudentModuleHistory

LOG = logging.getLogger(__name__)


class Command(BaseCommand):
    '''
    The fix here is to remove the "input_state" entry in the StudentModule objects of any problems that
    contain them.  No problem is yet making use of this, and the code should do the right thing if it's
    missing (by recreating an empty dict for its value).
    
    To narrow down the set of problems that might need fixing, the StudentModule
    objects to be checked is filtered down to those:

        created < '2013-03-29 16:30:00' (the problem must have been answered before the buggy code was reverted,
                                         on Prod and Edge)
        modified > '2013-03-28 22:00:00' (the problem must have been visited after the bug was introduced
                                          on Prod and Edge)
        state like '%input_state%' (the problem must have "input_state" set).
    '''

    num_visited = 0
    num_changed = 0
    num_hist_visited = 0
    num_hist_changed = 0

    option_list = BaseCommand.option_list + (
        make_option('--save',
                    action='store_true',
                    dest='save_changes',
                    default=False,
                    help='Persist the changes that were encountered.  If not set, no changes are saved.'), )

    def fix_studentmodules(self, save_changes):
        '''Identify the list of StudentModule objects that might need fixing, and then fix each one'''
        modules = StudentModule.objects.filter(modified__gt='2013-03-28 22:00:00',
                                               created__lt='2013-03-29 16:30:00',
                                               state__contains='input_state')

        for module in modules:
            self.remove_studentmodule_input_state(module, save_changes)

        LOG.info("Finished student modules:  updating {0} of {1} modules".format(self.num_changed, self.num_visited))

        hist_modules = StudentModuleHistory.objects.filter(created__gt='2013-03-28 22:00:00',
                                                           created__lt='2013-03-29 16:30:00',
                                                           state__contains='input_state')

        for hist_module in hist_modules:
            self.remove_studentmodulehistory_input_state(hist_module, save_changes)

        LOG.info("Finished student history modules:  updating {0} of {1} modules".format(self.num_hist_changed, self.num_hist_visited))
    
    @transaction.autocommit
    def remove_studentmodule_input_state(self, module, save_changes):
        ''' Fix the grade assigned to a StudentModule'''
        module_state = module.state
        if module_state is None:
            # not likely, since we filter on it.  But in general...
            LOG.info("No state found for {type} module {id} for student {student} in course {course_id}"
                     .format(type=module.module_type, id=module.module_state_key,
                             student=module.student.username, course_id=module.course_id))
            return

        state_dict = json.loads(module_state)
        self.num_visited += 1

        if 'input_state' not in state_dict:
            pass
        elif save_changes:
            # make the change and persist
            del state_dict['input_state']
            module.state = json.dumps(state_dict)
            module.save()
            self.num_changed += 1
        else:
            # don't make the change, but increment the count indicating the change would be made
            self.num_changed += 1

    @transaction.autocommit
    def remove_studentmodulehistory_input_state(self, module, save_changes):
        ''' Fix the grade assigned to a StudentModule'''
        module_state = module.state
        if module_state is None:
            # not likely, since we filter on it.  But in general...
            LOG.info("No state found for {type} module {id} for student {student} in course {course_id}"
                     .format(type=module.module_type, id=module.module_state_key,
                             student=module.student.username, course_id=module.course_id))
            return

        state_dict = json.loads(module_state)
        self.num_hist_visited += 1

        if 'input_state' not in state_dict:
            pass
        elif save_changes:
            # make the change and persist
            del state_dict['input_state']
            module.state = json.dumps(state_dict)
            module.save()
            self.num_hist_changed += 1
        else:
            # don't make the change, but increment the count indicating the change would be made
            self.num_hist_changed += 1

    def handle(self, **options):
        '''Handle management command request'''

        save_changes = options['save_changes']

        LOG.info("Starting run: save_changes = {0}".format(save_changes))

        self.fix_studentmodules(save_changes)

        LOG.info("Finished run:  updating {0} of {1} student modules".format(self.num_changed, self.num_visited))
        LOG.info("Finished run:  updating {0} of {1} student history modules".format(self.num_hist_changed, self.num_hist_visited))
