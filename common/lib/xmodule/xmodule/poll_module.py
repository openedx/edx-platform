"""Poll module is ungraded xmodule used by students to
to do set of polls.

On the client side we show:
If student does not yet anwered - Question with set of choices.
If student have answered - Question with statistics for each answers.
"""


import html
import json
import logging
from collections import OrderedDict
from copy import deepcopy

from pkg_resources import resource_string

import six
from lxml import etree
from openedx.core.djangolib.markup import Text, HTML
from xblock.fields import Boolean, Dict, List, Scope, String
from xmodule.mako_module import MakoModuleDescriptor
from xmodule.stringify import stringify_children
from xmodule.x_module import XModule
from xmodule.xml_module import XmlDescriptor

log = logging.getLogger(__name__)
_ = lambda text: text


class PollFields(object):
    # Name of poll to use in links to this poll
    display_name = String(
        help=_("The display name for this component."),
        scope=Scope.settings
    )

    voted = Boolean(
        help=_("Whether this student has voted on the poll"),
        scope=Scope.user_state,
        default=False
    )
    poll_answer = String(
        help=_("Student answer"),
        scope=Scope.user_state,
        default=''
    )
    poll_answers = Dict(
        help=_("Poll answers from all students"),
        scope=Scope.user_state_summary
    )

    # List of answers, in the form {'id': 'some id', 'text': 'the answer text'}
    answers = List(
        help=_("Poll answers from xml"),
        scope=Scope.content,
        default=[]
    )

    question = String(
        help=_("Poll question"),
        scope=Scope.content,
        default=''
    )


class PollModule(PollFields, XModule):
    """Poll Module"""
    js = {
        'js': [
            resource_string(__name__, 'js/src/javascript_loader.js'),
            resource_string(__name__, 'js/src/poll/poll.js'),
            resource_string(__name__, 'js/src/poll/poll_main.js')
        ]
    }
    css = {'scss': [resource_string(__name__, 'css/poll/display.scss')]}
    js_module_name = "Poll"

    def handle_ajax(self, dispatch, data):
        """Ajax handler.

        Args:
            dispatch: string request slug
            data: dict request data parameters

        Returns:
            json string
        """
        if dispatch in self.poll_answers and not self.voted:
            # FIXME: fix this, when xblock will support mutable types.
            # Now we use this hack.
            temp_poll_answers = self.poll_answers
            temp_poll_answers[dispatch] += 1
            self.poll_answers = temp_poll_answers

            self.voted = True
            self.poll_answer = dispatch
            return json.dumps({'poll_answers': self.poll_answers,
                               'total': sum(self.poll_answers.values()),
                               'callback': {'objectName': 'Conditional'}
                               })
        elif dispatch == 'get_state':
            return json.dumps({'poll_answer': self.poll_answer,
                               'poll_answers': self.poll_answers,
                               'total': sum(self.poll_answers.values())
                               })
        elif dispatch == 'reset_poll' and self.voted and \
                self.descriptor.xml_attributes.get('reset', 'True').lower() != 'false':
            self.voted = False

            # FIXME: fix this, when xblock will support mutable types.
            # Now we use this hack.
            temp_poll_answers = self.poll_answers
            temp_poll_answers[self.poll_answer] -= 1
            self.poll_answers = temp_poll_answers

            self.poll_answer = ''
            return json.dumps({'status': 'success'})
        else:  # return error message
            return json.dumps({'error': 'Unknown Command!'})

    def get_html(self):
        """Renders parameters to template."""
        params = {
            'element_id': self.location.html_id(),
            'element_class': self.location.block_type,
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
        # FIXME: hack for resolving caching `default={}` during definition
        # poll_answers field
        if self.poll_answers is None:
            self.poll_answers = {}

        answers_to_json = OrderedDict()

        # FIXME: fix this, when xblock support mutable types.
        # Now we use this hack.
        temp_poll_answers = self.poll_answers

        # Fill self.poll_answers, prepare data for template context.
        for answer in self.answers:
            # Set default count for answer = 0.
            if answer['id'] not in temp_poll_answers:
                temp_poll_answers[answer['id']] = 0
            answers_to_json[answer['id']] = html.escape(answer['text'], quote=False)
        self.poll_answers = temp_poll_answers

        return json.dumps({
            'answers': answers_to_json,
            'question': html.escape(self.question, quote=False),
            # to show answered poll after reload:
            'poll_answer': self.poll_answer,
            'poll_answers': self.poll_answers if self.voted else {},
            'total': sum(self.poll_answers.values()) if self.voted else 0,
            'reset': str(self.descriptor.xml_attributes.get('reset', 'true')).lower()
        })


class PollDescriptor(PollFields, MakoModuleDescriptor, XmlDescriptor):
    _tag_name = 'poll_question'
    _child_tag_name = 'answer'

    module_class = PollModule
    resources_dir = None

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        """Pull out the data into dictionary.

        Args:
            xml_object: xml from file.
            system: `system` object.

        Returns:
            (definition, children) - tuple
            definition - dict:
                {
                    'answers': <List of answers>,
                    'question': <Question string>
                }
        """
        # Check for presense of required tags in xml.
        if len(xml_object.xpath(cls._child_tag_name)) == 0:
            raise ValueError("Poll_question definition must include \
                at least one 'answer' tag")

        xml_object_copy = deepcopy(xml_object)
        answers = []
        for element_answer in xml_object_copy.findall(cls._child_tag_name):
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
        """Return an xml element representing to this definition."""
        poll_str = HTML('<{tag_name}>{text}</{tag_name}>').format(
            tag_name=self._tag_name, text=self.question)
        xml_object = etree.fromstring(poll_str)
        xml_object.set('display_name', self.display_name)

        def add_child(xml_obj, answer):
            # Escape answer text before adding to xml tree.
            answer_text = str(answer['text'])
            child_str = Text('{tag_begin}{text}{tag_end}').format(
                tag_begin=HTML('<{tag_name} id="{id}">').format(
                    tag_name=self._child_tag_name,
                    id=answer['id']
                ),
                text=answer_text,
                tag_end=HTML('</{tag_name}>').format(tag_name=self._child_tag_name)
            )
            child_node = etree.fromstring(child_str)
            xml_object.append(child_node)

        for answer in self.answers:
            add_child(xml_object, answer)

        return xml_object
