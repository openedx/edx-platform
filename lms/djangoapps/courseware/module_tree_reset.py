import json
import logging
import datetime
from collections import OrderedDict

import pytz
from django.db.models import Q
from django.db import transaction
from django.contrib.auth.models import User
from django.conf import settings
from django.dispatch import Signal
from django.core.cache import get_cache

from request_cache.middleware import RequestCache
from xmodule.modulestore.django import modulestore
from instructor.offline_gradecalc import student_grades
from courseware.models import StudentModule, StudentModuleHistory


log = logging.getLogger("mitx.module_tree_reset")


CACHE = get_cache('mongo_metadata_inheritance')
for store_name in settings.MODULESTORE:
    store = modulestore(store_name)
    store.metadata_inheritance_cache_subsystem = CACHE
    store.request_cache = RequestCache.get_request_cache()
    modulestore_update_signal = Signal(
        providing_args=['modulestore', 'course_id', 'location'])
    store.modulestore_update_signal = modulestore_update_signal


class TreeNode(object):
    def __init__(self, course_id, module, level, student):
        self.course_id = course_id
        self.module = module
        self.level = level
        self.student = student
        self.smstate = None
        if self.module.category in ['randomize', 'problem', 'problemset']:
            try:
                self.smstate = StudentModule.objects.get(
                    course_id=self.course_id,
                    module_state_key=self.module.location.url(),
                    student=student)
            except StudentModule.DoesNotExist:
                pass

    def __str__(self):
        s = "-" * self.level + ("> %s" % self.module.location.url())
        s += '  (%s)' % self.module.display_name

        if self.smstate is not None:
            s += ' [%s]' % self.smstate.state
        return s

    __repr__ = __str__


class TreeNodeSet(list):
    def __init__(self, course_id, module, ms, student):
        super(TreeNodeSet, self).__init__(self)
        self.course_id = course_id
        self.parent_module = module
        self.student = student
        self.get_tree(module, ms)
        self.get_modules_to_reset()

    def get_tree(self, module, ms, level=1):
        self.append(TreeNode(self.course_id, module, level, self.student))
        for child in getattr(module, 'children', []):
            m = ms.get_instance(self.course_id, child)
            if m is not None:
                self.get_tree(m, ms, level + 1)

    def get_modules_to_reset(self):
        self.rset = []
        self.pset = []
        for tn in self:
            if tn.module.category == 'randomize':
                self.rset.append(tn)
            elif tn.module.category in ['problem', 'problemset']:
                self.pset.append(tn)

    def reset_randomization(self, wipe_history=False):
        """
        Go through all <problem> and <randomize> modules in tree and reset
        their StudentModule state to empty.
        """
        msg = ("Resetting all <problem> and <randomize> in tree of parent "
               "module %s\n" % self.parent_module)
        for module in self.rset + self.pset:
            if module.smstate is not None:
                old_state = json.loads(module.smstate.state or '{}')
                state = {}
                msg += "    Resetting %s, old state=%s\n" % (module, state)
                if not wipe_history and 'history' in old_state:
                    state['history'] = old_state['history']
                # get_student_status uses this state but original code didn't
                # preserve it so leaving it commented for now
                # if 'position' in old_state:
                #     state['position'] = old_state['position']
                module.smstate.state = json.dumps(state)
                module.smstate.grade = None
                module.smstate.save()
        return msg


class DummyRequest(object):
    META = {}

    def __init__(self):
        return

    def get_host(self):
        return 'edx.mit.edu'

    def is_secure(self):
        return False


class StateInfo(object):
    def __init__(self):
        self.state = '{}'
        return


class ProctorModuleInfo(object):
    def __init__(self, course_id):
        self.ms = modulestore()
        self.course = self.ms.get_course(course_id)
        if not self.course:
            raise Exception("course does not exist: %s" % course_id)
        self.get_released_proctor_modules()

    def _get_student_obj(self, student):
        if isinstance(student, basestring):
            student = User.objects.get(username=student)
        return student

    def get_released_proctor_modules(self):
        chapters = []

        for loc in self.course.children:
            chapters.append(self.ms.get_instance(self.course.id, loc))

        # print "chapters:"
        # print [c.id for c in chapters]

        pmods = []
        for c in chapters:
            seq = self.ms.get_instance(self.course.id, c.children[0])
            if seq.category == 'proctor':
                pmods.append(seq)

        # print "proctor modules:"
        # print [x.id for x in pmods]

        now = datetime.datetime.now(pytz.utc)
        rpmods = [p for p in pmods if p.start < now]

        for rpmod in rpmods:
            # the problemset
            rpmod.ra_ps = self.ms.get_instance(self.course.id,
                                               rpmod.children[0])
            # the randomize
            rpmod.ra_rand = self.ms.get_instance(self.course.id,
                                                 rpmod.ra_ps.children[0])
            # the problem
            # rpmod.ra_prob = self.ms.get_instance(self.course.id,
            # rpmod.ra_rand.children[0])

        # print "released pmods"
        # print [x.id for x in rpmods]

        self.chapters = chapters
        self.pmods = pmods
        self.rpmods = rpmods
        return rpmods

    def get_grades(self, student, request=None):
        student = self._get_student_obj(student)
        if request is None:
            request = DummyRequest()
            request.user = student
            request.session = {}

        try:
            gradeset = student_grades(student, request, self.course,
                                      keep_raw_scores=False, use_offline=False)
        except Exception:
            log.exception("Failed to get grades for %s" % student)
            gradeset = []

        self.gradeset = gradeset
        return gradeset

    def get_student_status(self, student, debug=False):
        """
        For a given student, and for all released proctored modules, get
        StudentModule state for each, and see which randomized problem was
        selected for a student (if any).
        """
        student = self._get_student_obj(student)

        smstates = OrderedDict()

        # for debugging; flushes db cache
        if debug:
            try:
                transaction.commit()
            except Exception:
                log.debug("db cache flushed")

        # assume <proctor><problemset><randomized/></problemset></proctor>
        # structure
        for rpmod in self.rpmods:
            try:
                sm = StudentModule.objects.get(
                    module_state_key=rpmod.ra_rand.location.url(),
                    course_id=self.course.id,
                    student=student)  # randomize state
            except StudentModule.DoesNotExist:
                sm = StateInfo()
            sm.rpmod = rpmod
            try:
                ps_sm = StudentModule.objects.get(
                    module_state_key=rpmod.ra_ps.location.url(),
                    course_id=self.course.id,
                    student=student)  # problemset state
            except StudentModule.DoesNotExist:
                ps_sm = StateInfo()
            sm.ps_sm = ps_sm
            sm.score = None

            # get title (display_name) of problem assigned, if student had
            # started a problem base this on the "choice" from the randmize
            # module state
            state = json.loads(sm.state)
            sm.choice = state.get('choice')
            sm.history = state.get('history')
            if sm.choice is not None:
                try:
                    sm.problem = self.ms.get_instance(
                        self.course.id, sm.choice)
                    sm.problem_name = sm.problem.display_name
                except Exception:
                    log.exception("Failed to get rand child "
                                  "choice=%s for %s student=%s" %
                                  (sm.choice, rpmod.ra_rand, student))
                    sm.problem = None
                    sm.problem_name = None
            else:
                sm.problem = None
                sm.problem_name = None
            # the url_name should be like 'LS1' and be the same key used in the
            # grade scores
            smstates[rpmod.url_name] = sm

        self.smstates = smstates

        # get grades, match gradeset assignments with StudentModule states, and
        # put grades there
        self.get_grades(student)
        totaled_scores = self.gradeset['totaled_scores']
        try:
            assessments = totaled_scores['Assessment']
        except KeyError:
            assessments = []
            for assessment in totaled_scores:
                assessments.extend(totaled_scores[assessment])

        for score in assessments:
            if score.section in smstates:
                smstates[score.section].score = score

        s = 'State for student %s:\n' % student
        status = {}  # this can be turned into a JSON str for the proctor panel
        status['student'] = dict(username=student.username,
                                 name=student.profile.name, id=student.id)
        status['assignments'] = []

        for (name, sm) in smstates.iteritems():
            # this doesn't work, since score will always appear?
            # attempted = (sm.score is not None)

            # if student has visited the problemset then position will have
            # been set
            attempted = 'position' in sm.ps_sm.state
            if not attempted and sm.score is not None and sm.score.earned:
                attempted = True
            visited = False
            if sm.choice and sm.history:
                visited = sm.choice in sm.history

            earned = (sm.score.earned if sm.score is not None else None)
            possible = (sm.score.possible if sm.score is not None else None)
            stat = dict(name=name, assignment=sm.rpmod.ra_ps.display_name,
                        pm_sm=sm.ps_sm.state, choice=sm.choice,
                        history=sm.history,
                        problem=sm.problem_name,
                        attempted=attempted,
                        visited=visited,
                        earned=earned,
                        possible=possible,
                        proctor_loc=sm.rpmod.location.url())
            status['assignments'].append(stat)
            s += "[%s] %s -> %s (%s) %s [%s]\n" % (name, stat['assignment'],
                                                   stat['pm_sm'], sm.choice,
                                                   sm.problem_name, sm.score)
        self.status = status
        self.status_str = s
        return status

    def get_student_grades(self, student):
        """
        Return student grades for assessments as a dict suitable for CSV file
        output, with id, name, username, prob1, grade1, prob2, grade2, ...
        where grade1 = points earned on assignment LS1, or '' if not attempted
        and prob1 = problem which was assigned or '' if not attempted
        """
        student = self._get_student_obj(student)
        status = self.get_student_status(student)
        ret = OrderedDict()
        ret['id'] = student.id
        ret['name'] = student.profile.name
        # ret['username'] = student.username
        ret['email'] = student.email

        for stat in status['assignments']:
            if stat['attempted']:
                ret["problem_%s" % stat['name']] = stat['problem']
                ret["grade_%s" % stat['name']] = stat['earned']
            else:
                ret["problem_%s" % stat['name']] = ''
                ret["grade_%s" % stat['name']] = ''
        return ret

    def proctor_reset(self, student, proctor_loc,
                      wipe_randomize_history=False, student_status=None):
        student = self._get_student_obj(student)
        status = student_status or self.get_student_status(student)
        assignments = status['assignments']
        try:
            ass = [i for i in assignments if i['proctor_loc'] == proctor_loc]
            assert len(ass) == 1
            ass = ass.pop()
        except AssertionError:
            raise Exception("proctor_loc = %s not found!" % proctor_loc)
        if ass['visited'] and ass['earned'] != ass['possible']:
            log.info('Resetting %s for student %s' %
                     (ass['name'], student.username))
            pmod = self.ms.get_instance(self.course.id, proctor_loc)
            tnset = TreeNodeSet(self.course.id, pmod, self.ms, student)
            msg = tnset.reset_randomization(wipe_history=wipe_randomize_history)
            log.debug(msg)
            return msg

    def get_assignments_attempted_and_failed(self, student, reset=False,
                                             wipe_randomize_history=False):
        student = self._get_student_obj(student)
        status = self.get_student_status(student)
        failed = [a for a in status['assignments'] if a['visited'] and
                  a['earned'] != a['possible']]
        for f in failed:
            log.info(
                "Student %s Assignment %s attempted '%s' but failed "
                "(%s/%s)" % (student.username, f['name'], f['problem'],
                             f['earned'], f['possible']))
            if reset:
                try:
                    self.proctor_reset(
                        student, f['proctor_loc'], student_status=status,
                        wipe_randomize_history=wipe_randomize_history)
                except Exception:
                    log.exception("Failed to do reset of %s for %s" %
                                  (f['assignment'], student))
        return failed

    def submission_history(self, student, locations):
        """
        Return history of all submission attempts by a student for a list of
        problems.
        """
        student = self._get_student_obj(student)
        student_modules = StudentModule.objects.filter(
            course_id=self.course.id,
            module_state_key__in=locations,
            student_id=student.id)

        history_entries = StudentModuleHistory.objects.filter(
            Q(state__contains='"attempts"') &
            Q(state__contains='"correct_map"') &
            Q(state__contains='"student_answers"'),
            student_module__in=student_modules, grade__isnull=False,
            max_grade__isnull=False,
        ).order_by('-id')

        seen_states = []
        entries = []

        for entry in history_entries:
            state = json.loads(entry.state)
            cmap = state['correct_map']
            real_grade = len([i for i in cmap.values() if
                              i['correctness'] == 'correct'])
            if entry.grade != real_grade:
                continue
            elif state in seen_states:
                continue
            else:
                seen_states.append(state)
                entries.append(entry)

        context = {
            'history_entries': entries,
            'username': student.username,
            'locations': locations,
            'course_id': self.course.id
        }

        return context
