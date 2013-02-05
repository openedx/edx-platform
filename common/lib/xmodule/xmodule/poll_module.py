"""Poll module is ungraded xmodule used by students to
to do set of polls.

Poll module contains a nummber of 2 - steps basic sequences. Every sequence
has data from all previous sequences. Selection of sequences can be in
control block.

Basic sequence:
`
0. Control block
    a) get data from any previous sequence
    b) if block
    c) link to sequence


1. First. - must be, always visible
If student does not yet anwered - Question
If student have not answered - Question with statistics (yes/no)

2. Second - optional, if student does not yet answered on 1st - hidden
If student answers first time - show plot with statistics from
answer from other users.

"""

import json
import logging
import cgi
from copy import deepcopy

from lxml import html, etree
from pkg_resources import resource_string

from xmodule.x_module import XModule
from xmodule.stringify import stringify_children
from xmodule.mako_module import MakoModuleDescriptor
from xmodule.xml_module import XmlDescriptor
from xblock.core import Integer, Scope, String, List, Object, Boolean

log = logging.getLogger(__name__)


class PollModule(XModule):
    """Poll Module"""
    js = {
      'coffee': [resource_string(__name__, 'js/src/javascript_loader.coffee')],
      'js': [resource_string(__name__, 'js/src/poll/logme.js'),
             resource_string(__name__, 'js/src/poll/poll.js'),
             resource_string(__name__, 'js/src/poll/poll_main.js')]
         }
    css = {'scss': [resource_string(__name__, 'css/poll/display.scss')]}
    js_module_name = "Poll"

    # name of poll to use in links to this poll
    display_name = String(help="Display name for this module", scope=Scope.settings)

    voted = Boolean(help="Whether this student has voted on the poll", scope=Scope.student_state, default=False)
    poll_answer = String(help="Student answer", scope=Scope.student_state, default='')
    poll_answers = Object(help="All possible answers for the poll", scope=Scope.content, default={})

    xml_object = Object(scope=Scope.content)  # poll xml


    def handle_ajax(self, dispatch, get):
        """Ajax handler.

        Args:
            dispatch: request slug
            get: request get parameters

        Returns:
            dict
        """
        if dispatch in self.poll_answers and not self.voted:
            tmp = {}
            for key in self.poll_answers:
                tmp[key] = self.poll_answers[key]
            tmp[dispatch] += 1
            self.voted = True
            self.poll_answer = dispatch
            self.poll_answers = tmp
            return json.dumps({'poll_answers': self.poll_answers,
                               'total': sum(self.poll_answers.values()),
                               'callback': {'objectName': 'Conditional'}
                               })
        return json.dumps({'error': 'Unknown Command!'})

    def get_html(self):
        """Renders parameters to template."""
        params = {
                  'element_id': self.location.html_id(),
                  'element_class': self.location.category,
                  'ajax_url': self.system.ajax_url,
                  'configuration_json': self.dump_poll(),
                  }
        self.content = self.system.render_template('poll.html', params)
        return self.content

    def dump_poll(self):
        """     """
        # import ipdb; ipdb.set_trace()
        # self.poll_answers['Yes']=2
        xml_object_copy = deepcopy(self.xml_object)
        answers_to_json = {}
        #workaround
        tmp={}
        for key in self.poll_answers:
            tmp[key] = self.poll_answers[key]
        for element_answer in xml_object_copy.findall('answer'):
            answer = element_answer.get('id', None)
            if answer:
                if answer not in tmp:
                    tmp[answer] = 0
                answers_to_json[answer] = \
                    cgi.escape(stringify_children(element_answer))
            xml_object_copy.remove(element_answer)
        self.poll_answers = tmp
        return json.dumps({'answers': answers_to_json,
              'question': cgi.escape(stringify_children(xml_object_copy)),
              # to show answered poll after reload:
                'poll_answer': '',  # self.poll_answer,
                'poll_answers': self.poll_answers if self.voted else {},
                'total': sum(self.poll_answers.values()) if self.voted else ''})


class PollDescriptor(MakoModuleDescriptor, XmlDescriptor):
    module_class = PollModule
    template_dir_name = 'poll'
    stores_state = True

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        """Pull out the data into dictionary.

        Args:
            xml_object: xml from file.
            system: `system` object.

        Returns:
            dict
        """
        # check for presense of required tags in xml
        if len(xml_object.xpath('answer')) == 0:
            raise ValueError("Poll_question definition must include \
                at least one 'answer' tag")

        return {'xml_object': xml_object}, []

    def definition_to_xml(self, resource_fs):
        """Return an xml element representing this definition."""
        #  TODO test and fix
        xml_object = etree.Element('poll_question')

        def add_child(k):
            child_str = '<{tag}>{body}</{tag}>'.format(tag=k, body=self.definition[k])
            child_node = etree.fromstring(child_str)
            xml_object.append(child_node)

        for child in ['render', 'sequence']:
            add_child(child)

        return xml_object
