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


import cgi
import json
import logging
from copy import deepcopy

from lxml import etree
from pkg_resources import resource_string

from xmodule.x_module import XModule
from xmodule.stringify import stringify_children
from xmodule.mako_module import MakoModuleDescriptor
from xmodule.xml_module import XmlDescriptor
from xblock.core import Scope, String, Object, Boolean, List

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

    answers = List(help="Poll answers", scope=Scope.content, default=[])
    question = String(help="Poll question", scope=Scope.content, default='')

    def handle_ajax(self, dispatch, get):
        """Ajax handler.

        Args:
            dispatch: request slug
            get: request get parameters

        Returns:
            dict
        """
        if dispatch in self.poll_answers and not self.voted:
            temp_poll_answers = self.poll_answers
            temp_poll_answers[dispatch] += 1
            self.voted = True
            self.poll_answer = dispatch
            self.poll_answers = temp_poll_answers
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
        """Dump poll information.

        Returns:
            string - Serialize json.
        """
        answers_to_json = {}
        #workaround
        temp_poll_answers = self.poll_answers
         # Fill self.poll_answers, prepare data for template context.
        for answer in self.answers:
            if answer['id'] not in temp_poll_answers:
                temp_poll_answers[answer['id']] = 0
            answers_to_json[answer['id']] = cgi.escape(answer['text'])
        self.poll_answers = temp_poll_answers
        return json.dumps({'answers': answers_to_json,
            'question': cgi.escape(self.question),
            # to show answered poll after reload:
            'poll_answer': self.poll_answer,
            'poll_answers': self.poll_answers if self.voted else {},
            'total': sum(self.poll_answers.values()) if self.voted else 0})


class PollDescriptor(MakoModuleDescriptor, XmlDescriptor):
    module_class = PollModule
    template_dir_name = 'poll'
    stores_state = True

    answers = List(help="Poll answers", scope=Scope.content, default=[])
    question = String(help="Poll question", scope=Scope.content, default='')
    display_name = String(help="Display name for this module", scope=Scope.settings)
    id = String(help="ID attribute for this module", scope=Scope.settings)

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        """Pull out the data into dictionary.

        Args:
            xml_object: xml from file.
            system: `system` object.

        Returns:
            (definition, children) - tuple
            definition - dict
            children - list
        """
        # check for presense of required tags in xml
        if len(xml_object.xpath('answer')) == 0:
            raise ValueError("Poll_question definition must include \
                at least one 'answer' tag")

        xml_object_copy = deepcopy(xml_object)
        answers = []
        for element_answer in xml_object_copy.findall('answer'):
            answer_id = element_answer.get('id', None)
            if answer_id:
                answers.append({
                    'id': answer_id,
                    'text': stringify_children(element_answer)
                })
            xml_object_copy.remove(element_answer)

        definition = {
            'answers': answers,
            'question': stringify_children(xml_object_copy)
        }
        children = []

        return (definition, children)

    def definition_to_xml(self, resource_fs):
        """Return an xml element representing this definition."""
        poll_str = '<poll_question>{0}</poll_question>'.format(self.question)
        xml_object = etree.fromstring(poll_str)
        xml_object.set('display_name', self.display_name)
        xml_object.set('id', self.id)

        def add_child(xml_obj, answer):
            child_str = '<answer id="{id}">{text}</answer>'.format(
                id=answer['id'], text=answer['text'])
            child_node = etree.fromstring(child_str)
            xml_object.append(child_node)

        for answer in self.answers:
            add_child(xml_object, answer)

        return xml_object
