import sys
import json
import logging
import urlparse
import requests

from lxml import etree
from pkg_resources import resource_string

from xmodule.x_module import XModule
from xmodule.seq_module import SequenceDescriptor

from xblock.fields import Scope, String, Boolean
from xblock.fragment import Fragment

try:
    from courseware import module_tree_reset
except ImportError:
    # TODO: this is an ugly hack to get around courseware import error during
    # static asset generation. fix this later some how
    if 'xmodule_assets' not in ' '.join(sys.argv):
        raise


log = logging.getLogger('mitx.' + __name__)


class ProctorPanel(object):
    '''
    Interface to proctor panel system, which determines if a given proctored item
    (specified by its procset_name) is released to a given student.

    The LMS configuration should come with a dict which specifies the proctor panel
    server information, eg:

        PROCTOR_PANEL_INTERFACE = {
            'url' : "http://192.168.42.6",
            'username' : 'lms',
            'password' : 'abcd',
        }
    '''
    def __init__(self, user, proc_url, proc_user, proc_pass, procset_name):
        self.proc_url = proc_url
        self.proc_user = proc_user
        self.proc_pass = proc_pass
        self.procset_name = procset_name
        self.user = user
        self.ses = requests.session()

    def _make_request(self, url, method="GET", data=None, json=True):
        ret = self.ses.request(
            method=method, url=urlparse.urljoin(self.proc_url, url),
            verify=False, data=data, auth=(self.proc_user, self.proc_pass),
            params={'problem': self.procset_name})
        if json:
            try:
                data = ret.json()
            except Exception:
                log.error('bad return from proctor panel: '
                          'ret.content={0}'.format(ret.content))
                data = {}
        else:
            data = ret.content
        return data

    def request(self, json=True):
        data = dict(uname=self.user.username, name=self.user.profile.name)
        return self._make_request('cmd/request/%s' % self.user.id,
                                  method='POST', data=data, json=json)

    def status(self, json=True):
        return self._make_request('cmd/status/%s' % self.user.id, json=json)

    def is_released(self):
        retdata = self.status()
        return retdata.get('enabled', False)


class ProctorFields(object):
    # display_name = String(
    #     display_name="Display Name",
    #     help="This name appears in the grades progress page",
    #     scope=Scope.settings,
    #     default="Proctored Module"
    # )
    procset_name = String(help="Name of this proctored set",
                          scope=Scope.settings)
    staff_release = Boolean(help="True if staff forced release independent "
                            "of proctor panel", default=False,
                            scope=Scope.user_state)
    proctor_url = String(help="proctor server URL", scope=Scope.settings)
    proctor_user = String(help="proctor server username", scope=Scope.settings)
    proctor_password = String(help="proctor server password",
                              scope=Scope.settings)


class ProctorModule(ProctorFields, XModule):
    """
    Releases modules for viewing depending on proctor panel.

    The proctor panel is a separate application which knows the mapping between
    user_id's and usernames, and whether a given problem should be released for
    access by that student or not.

    The idea is that a course staff member is proctoring an exam provided in
    the edX system.  After the staff member verifies a student's identity, the
    staff member releases the exam to the student, via the proctor panel.  Once
    the student is done, or the elapsed time runs out, exam access closes.

    Example:
    <proctor procset_name="Proctored Exam 1">
    <sequential url_name="exam1" />
    </proctor>
    """

    js = {
        'coffee': [
            resource_string(__name__, 'js/src/javascript_loader.coffee'),
            resource_string(__name__, 'js/src/conditional/display.coffee')
        ],
        'js': [
            resource_string(__name__, 'js/src/collapsible.js')
        ],
    }

    js_module_name = "Conditional"
    css = {'scss': [resource_string(__name__, 'css/capa/display.scss')]}

    def __init__(self, *args, **kwargs):
        super(ProctorModule, self).__init__(*args, **kwargs)
        # check proctor panel to see if this should be released
        user = self.runtime.get_real_user(self.runtime.anonymous_student_id)
        self.pp = ProctorPanel(user, self.proctor_url, self.proctor_user,
                               self.proctor_password, self.procset_name)
        self.child_descriptor = self.descriptor.get_children()[0]
        log.debug("proctor module children (should only be 1): %s",
                  self.get_children())
        self.child = self.get_children()[0]
        log.info('Proctor module child={0}'.format(self.child))
        log.info('Proctor module child display_name={0}'.format(self.child.display_name))
        # TODO: This attr is read-only now - need to figure out if/why this is
        # needed and find a fix if necessary (disabling doesnt appear to break
        # anything)
        # self.display_name = self.child.display_name

    def is_released(self):
        released = None
        if self.staff_release:
            released = True
        else:
            released = self.pp.is_released()
        log.info("is_released: %s" % released)
        return released

    def get_child_descriptors(self):
        """
        For grading--return just the child.
        """
        return [self.child_descriptor]

    def _template_ctx(self):
        ctx = {
            'id': self.id,
            'pp': self.pp,
            'name': self.display_name or self.procset_name,
            'element_id': self.location.html_id(),
            'location': self.location,
            'ajax_url': self.runtime.ajax_url,
            'is_staff': self.runtime.user_is_staff,
            'staff_release': self.staff_release,
            'is_released': self.is_released(),
            'child_html': None,
        }
        return ctx

    def not_released_html(self):
        return Fragment(self.runtime.render_template('proctor.html',
                                                     self._template_ctx()))

    def student_view(self, context):
        proc_ctx = self._template_ctx()
        # for sequential module, just return HTML (no ajax container)
        categories = ['sequential', 'videosequence', 'problemset', 'randomize']
        if self.child.category in categories:
            proc_ctx['child_html'] = self.child.render('student_view',
                                                       context).content
            return Fragment(self.runtime.render_template(
                'proctor.html', proc_ctx))
        # return ajax container, so that we can dynamically check for
        # is_released changing
        proc_ctx['depends'] = ''
        return Fragment(self.runtime.render_template('conditional_ajax.html',
                                                     proc_ctx))

    def _str_to_bool(self, v):
        return v.lower() == 'true'

    def handle_ajax(self, dispatch, data):
        if self.runtime.user_is_staff:
            if dispatch == 'override':
                enabled = self._str_to_bool(data.get('enabled', 'false'))
                self.staff_release = enabled
                return json.dumps({'enabled': enabled})

            # Proctor Student Admin URLs (STAFF ONLY)
            if dispatch == 'reset':
                username = data.get("username")
                wipe_history = data.get("wipe_history") == "on"
                return self.reset(username, wipe_history=wipe_history)
            #if dispatch == 'status':
                #return self.status()
            # if dispatch == 'grades':
            #     return self.grades()

        # Proctor Panel requests (ALL USERS)
        if dispatch == 'request':
            return self.pp.request(json=False)
        if dispatch == 'status':
            return self.pp.status(json=False)

        if not self.is_released():  # check each time we do get_html()
            html = self.not_released_html()
            return json.dumps({'html': [html], 'message': True})
        html = [child.get_html() for child in self.get_display_items()]
        return json.dumps({'html': html})

    def get_icon_class(self):
        return self.child.get_icon_class() if self.child else 'other'

    def reset(self, username, wipe_history=False):
        try:
            pminfo = module_tree_reset.ProctorModuleInfo(self.runtime.course_id)
            pminfo.get_assignments_attempted_and_failed(
                username, reset=True, wipe_randomize_history=wipe_history)
            return self.status(username)
        except Exception as exc:
            return json.dumps({"error": str(exc)})

    def status(self, username):
        try:
            student = self.pp.user
            pminfo = module_tree_reset.ProctorModuleInfo(self.runtime.course_id)
            status = pminfo.get_student_status(username)
        except Exception as err:
            log.exception("Failed to get status for %s" % student)
            status = {'msg': 'Error getting grades for %s' % student,
                      'error': True, 'errstr': str(err)}
        return json.dumps(status)

    # TODO: investigate whether this is needed or not
    #
    # def grades(self):
    #     student = self.pp.user
    #     ms = modulestore()
    #     course = ms.get_item(
    #         'i4x://MITx/3.091r-exam/course/2013_Fall_residential_exam')
    #     try:
    #         gradeset = student_grades(student, request, course,
    #                                   keep_raw_scores=False, use_offline=False)
    #     except Exception:
    #         log.exception("Failed to get grades for %s" % student)
    #         return json.dumps(
    #             {'msg': 'Error getting grades for %s' % student,
    #              'error': True})
    #     grades = gradeset['totaled_scores']
    #     grades['student_id'] = student.id
    #     return json.dumps(grades)


class ProctorDescriptor(ProctorFields, SequenceDescriptor):
    # the editing interface can be the same as for sequences -- just a container
    module_class = ProctorModule

    filename_extension = "xml"

    def definition_to_xml(self, resource_fs):

        xml_object = etree.Element('proctor')
        for child in self.get_children():
            self.runtime.add_block_as_child_node(child, xml_object)
        return xml_object
