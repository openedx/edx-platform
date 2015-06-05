'''
This is a one-off command aimed at fixing a temporary problem encountered where input_state was added to
the same dict object in capa problems, so was accumulating.  The fix is simply to remove input_state entry
from state for all problems in the affected date range.
'''

import json
import logging
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from courseware.models import StudentModule
from courseware.user_state_client import DjangoXBlockUserStateClient

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

    This filtering is done on the production database replica, so that the larger select queries don't lock
    the real production database.  The list of id values for Student Modules is written to a file, and the
    file is passed into this command.  The sql file passed to mysql contains:

        select sm.id from courseware_studentmodule sm
            where sm.modified > "2013-03-28 22:00:00"
                and sm.created < "2013-03-29 16:30:00"
                and sm.state like "%input_state%"
                and sm.module_type = 'problem';

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
                    help='Persist the changes that were encountered.  If not set, no changes are saved.'),
    )

    def fix_studentmodules_in_list(self, save_changes, idlist_path):
        '''Read in the list of StudentModule objects that might need fixing, and then fix each one'''

        # open file and read id values from it:
        for line in open(idlist_path, 'r'):
            student_module_id = line.strip()
            # skip the header, if present:
            if student_module_id == 'id':
                continue
            try:
                module = StudentModule.objects.select_related('student').get(id=student_module_id)
            except StudentModule.DoesNotExist:
                LOG.error(u"Unable to find student module with id = %s: skipping... ", student_module_id)
                continue
            self.remove_studentmodule_input_state(module, save_changes)

            user_state_client = DjangoXBlockUserStateClient()
            hist_modules = user_state_client.get_history(module.student.username, module.module_state_key)

            for hist_module in hist_modules:
                self.remove_studentmodulehistory_input_state(hist_module, save_changes)

            if self.num_visited % 1000 == 0:
                LOG.info(" Progress: updated {0} of {1} student modules".format(self.num_changed, self.num_visited))
                LOG.info(" Progress: updated {0} of {1} student history modules".format(self.num_hist_changed,
                                                                                        self.num_hist_visited))

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

    def handle(self, *args, **options):
        '''Handle management command request'''
        if len(args) != 1:
            raise CommandError("missing idlist file")
        idlist_path = args[0]
        save_changes = options['save_changes']
        LOG.info("Starting run:  reading from idlist file {0}; save_changes = {1}".format(idlist_path, save_changes))

        self.fix_studentmodules_in_list(save_changes, idlist_path)

        LOG.info("Finished run:  updating {0} of {1} student modules".format(self.num_changed, self.num_visited))
        LOG.info("Finished run:  updating {0} of {1} student history modules".format(self.num_hist_changed,
                                                                                     self.num_hist_visited))
