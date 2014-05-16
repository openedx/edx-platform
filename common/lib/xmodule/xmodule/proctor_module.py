import json
import logging
import requests

from lxml import etree
from pkg_resources import resource_string

from django.conf import settings
from django.contrib.auth.models import User

from xmodule.x_module import XModule
from xmodule.seq_module import SequenceDescriptor

from xblock.fields import Scope, String, Boolean
from xblock.fragment import Fragment

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

    ProctorPanelInterface = getattr(settings, 'PROCTOR_PANEL_INTERFACE', {})
    ProctorPanelServer = ProctorPanelInterface.get('url', "")

    def __init__(self, user_id, procset_name):

        self.user_id = user_id
        self.procset_name = procset_name
        self.ses = requests.session()
        self.user = User.objects.get(pk=user_id)

    def is_released(self):
        #url = '{2}/cmd/status/{0}/{1}'.format(self.user_id, self.procset_name, self.ProctorPanelServer)
        url = '{1}/cmd/status/{0}'.format(self.user_id, self.ProctorPanelServer)
        log.info('ProctorPanel url={0}'.format(url))
        #ret = self.ses.post(url, data={'userid' : self.user_id, 'urlname': self.procset_name}, verify=False)
        auth = (self.ProctorPanelInterface.get('username'), self.ProctorPanelInterface.get('password'))
        ret = self.ses.get(url, verify=False, auth=auth, params={'problem': self.procset_name})
        try:
            retdat = json.loads(ret.content)
        except Exception:
            log.error('bad return from proctor panel: ret.content={0}'.format(ret.content))
            retdat = {}

        log.info('ProctorPanel retdat={0}'.format(retdat))
        enabled = retdat.get('enabled', False)
        return enabled


class ProctorFields(object):
    #display_name = String(
    #    display_name="Display Name",
    #    help="This name appears in the grades progress page",
    #    scope=Scope.settings,
    #    default="Proctored Module"
    #)
    procset_name = String(help="Name of this proctored set", scope=Scope.settings)
    staff_release = Boolean(help="True if staff forced release independent of proctor panel",
                       default=False, scope=Scope.user_state)


class ProctorModule(ProctorFields, XModule):
    """
    Releases modules for viewing depending on proctor panel.

    The proctor panel is a separate application which knows the mapping between user_id's and usernames,
    and whether a given problem should be released for access by that student or not.

    The idea is that a course staff member is proctoring an exam provided in the edX system.
    After the staff member verifies a student's identity, the staff member releases the exam
    to the student, via the proctor panel.  Once the student is done, or the elapsed time
    runs out, exam access closes.

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
        user_id = self.system.seed
        self.pp = ProctorPanel(user_id, self.procset_name)

        self.child_descriptor = self.descriptor.get_children()[0]
        log.debug("children of proctor module (should be only 1): %s", self.get_children())
        self.child = self.get_children()[0]

        log.info('Proctor module child={0}'.format(self.child))
        log.info('Proctor module child display_name={0}'.format(self.child.display_name))
        # TODO: This attr is read-only now - need to figure out if/why this is
        # needed and find a fix if necessary (disabling doesnt appear to break
        # anything)
        #self.display_name = self.child.display_name


    def is_released(self):
        if self.staff_release:
            return True
        return self.pp.is_released()


    def get_child_descriptors(self):
        """
        For grading--return just the child.
        """
        return [self.child_descriptor]


    def not_released_html(self):
        return Fragment(self.system.render_template('proctor_release.html', {
                'element_id': self.location.html_id(),
                'id': self.id,
                'name': self.display_name or self.procset_name,
                'pp': self.pp,
                'location': self.location,
                'ajax_url': self.system.ajax_url,
                'is_staff': self.system.user_is_staff,
        }))


    def student_view(self, context):
        if not self.is_released():	# check for release each time we do get_html()
            log.info('is_released False')
            return self.not_released_html()
            # return "<div>%s not yet released</div>" % self.display_name

        log.info('is_released True')

        # for sequential module, just return HTML (no ajax container)
        if self.child.category in ['sequential', 'videosequence', 'problemset', 'randomize']:
            html = self.child.render('student_view', context)
            if self.staff_release:
                dishtml = self.system.render_template('proctor_disable.html', {
                        'element_id': self.location.html_id(),
                        'is_staff': self.system.user_is_staff,
                        'ajax_url': self.system.ajax_url,
                        })
                html.content = dishtml + html.content
            return html

        # return ajax container, so that we can dynamically check for is_released changing
        return Fragment(self.system.render_template('conditional_ajax.html', {
            'element_id': self.location.html_id(),
            'id': self.id,
            'ajax_url': self.system.ajax_url,
            'depends': '',
        }))



    def handle_ajax(self, _dispatch, _data):
        if self.system.user_is_staff and _dispatch=='release':
            self.staff_release = True
            # return '<html><head><META HTTP-EQUIV="refresh" CONTENT="15"></head><body>Release successful</body></html>'
            return json.dumps({'html': 'staff_release successful'})
        if self.system.user_is_staff and _dispatch=='disable':
            self.staff_release = False
            return json.dumps({'html': 'staff_disable successful'})
            # return '<html><head><META HTTP-EQUIV="refresh" CONTENT="15"></head><body>Disable successful</body></html>'

        if not self.is_released():	# check for release each time we do get_html()
            log.info('is_released False')
            # html = "<div>%s not yet released</div>" % self.display_name
            html = self.not_released_html()
            return json.dumps({'html': [html], 'message': bool(True)})
        html = [child.get_html() for child in self.get_display_items()]

        log.info('is_released True')
        return json.dumps({'html': html})


    def get_icon_class(self):
        return self.child.get_icon_class() if self.child else 'other'


class ProctorDescriptor(ProctorFields, SequenceDescriptor):
    # the editing interface can be the same as for sequences -- just a container
    module_class = ProctorModule

    filename_extension = "xml"


    def definition_to_xml(self, resource_fs):

        xml_object = etree.Element('proctor')
        for child in self.get_children():
            self.runtime.add_block_as_child_node(child, xml_object)
        return xml_object
