"""
Poll module is ungraded xmodule used by students to
to do set of polls.

Poll module contains a nummber of 2 - steps basic sequences. Every sequence
has data from all previous sequences. Selection of sequences can be in
control block.

Basic sequence:

0. Control block
    a) get data from any previous sequence
    b) if block
    c) link to sequence


1. First. - must be, always visible
If student does not yet anwered - Question
If stundent have not answered - Question with statistics (yes/no)

2. Second - optional, if student does not yet answered on 1st - hidden
If student answers first time - show plot with statistics from
answer from other users.

"""

import json
import logging
import cgi

from lxml import html, etree
from pkg_resources import resource_string

from xmodule.x_module import XModule
from xmodule.stringify import stringify_children
from xmodule.mako_module import MakoModuleDescriptor
from xmodule.xml_module import XmlDescriptor
from xblock.core import Integer, Scope, String, List  # , Boolean

log = logging.getLogger(__name__)


class PollModule(XModule):
    ''' Poll Module
    '''
    js = {
      'coffee': [resource_string(__name__, 'js/src/javascript_loader.coffee')],
      'js': [resource_string(__name__, 'js/src/poll/poll.js'),
             resource_string(__name__, 'js/src/poll/poll_main.js')]
         }
    css = {'scss': [resource_string(__name__, 'css/poll/display.scss')]}
    js_module_name = "Poll"

    # poll_id =
    upvotes = Integer(help="Number of upvotes this poll has recieved", scope=Scope.content, default=0)
    downvotes = Integer(help="Number of downvotes this poll has recieved", scope=Scope.content, default=0)
    # voted = Boolean(help="Whether this student has voted on the poll", scope=Scope.student_state, default=False)
    # poll_id_list = List(help="Number of upvotes this poll has recieved", scope=Scope.content, default=[])
    # poll_up_list = List(help="Number of upvotes this poll has recieved", scope=Scope.content, default=[])
    # poll_down_list = List(help="Number of upvotes this poll has recieved", scope=Scope.content, default=[])

    xml_object = String(scope=Scope.content)

    def handle_ajax(self, dispatch, get):
        ''' '''
        if dispatch == 'upvote':
            self.upvotes += 1
            # self.voted = True
            return json.dumps({'upvotes': self.upvotes, 'downvotes': self.downvote})
        elif dispatch == 'downvote':
            self.downvotes += 1
            # self.voted = True
            return json.dumps({'upvotes': self.upvotes, 'downvotes': self.downvote})

        return json.dumps({'error': 'Unknown Command!'})

    def get_html(self):
        """ Renders parameters to template. """
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
        return json.dumps({'poll_chain':
                          [{'question': cgi.escape(stringify_children(q)),
                            'id':          q.get('id'),
                            'upvote_id':   q.get('upvote', ""),
                            'downvote_id': q.get('downvote', ""),
                            'show_stats':  q.get('show_stats', "yes")}
                            for q in self.xml_object.xpath('question')]})


class PollDescriptor(MakoModuleDescriptor, XmlDescriptor):
    module_class = PollModule
    template_dir_name = 'poll'
    stores_state = True

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        """
        Pull out the data into dictionary.

        Args:
            xml_object: xml from file.

        Returns:
            dict
        """
        # check for presense of required tags in xml
        if len(xml_object.xpath('question')) == 0:
            raise ValueError("Poll definition must include \
                at least one 'question' tag")

        return {'xml_object': xml_object}, []

    def definition_to_xml(self, resource_fs):
        '''Return an xml element representing this definition.'''
        xml_object = etree.Element('graphical_slider_tool')

        def add_child(k):
            child_str = '<{tag}>{body}</{tag}>'.format(tag=k, body=self.definition[k])
            child_node = etree.fromstring(child_str)
            xml_object.append(child_node)

        for child in ['render', 'sequence']:
            add_child(child)

        return
