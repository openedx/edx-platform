"""Word cloud is ungraded xblock used by students to
generate and view word cloud..

On the client side we show:
If student does not yet anwered - five text inputs.
If student have answered - words he entered and cloud.

Stunent can change his answer.
"""

import cgi
import json
import logging
from copy import deepcopy
from collections import OrderedDict

from lxml import etree
from pkg_resources import resource_string

from xmodule.x_module import XModule
from xmodule.stringify import stringify_children
from xmodule.mako_module import MakoModuleDescriptor
from xmodule.xml_module import XmlDescriptor
from xblock.core import Scope, String, Object, Boolean, List, Integer

log = logging.getLogger(__name__)


class WordCloudFields(object):
    # Name of poll to use in links to this poll
    display_name = String(help="Display name for this module", scope=Scope.settings)
    num_inputs = Integer(help="Number of inputs", scope=Scope.settings)

    submitted = Boolean(help="Whether this student has voted on the poll", scope=Scope.student_state, default=False)
    student_words= List(help="Student answer", scope=Scope.student_state, default=[])
    all_words = Object(help="All possible words from other students", scope=Scope.content)
    top_words = Object(help="Top N words for word cloud", scope=Scope.content)
    top_low_border = Integer(help="Number to distinguish top from all words", scope=Scope.content)

class WordCloudModule(WordCloudFields, XModule):
    """WordCloud Module"""
    js = {
      'coffee': [resource_string(__name__, 'js/src/javascript_loader.coffee')],
      'js': [resource_string(__name__, 'js/src/word_cloud/logme.js'),
             resource_string(__name__, 'js/src/word_cloud/word_cloud.js'),
             resource_string(__name__, 'js/src/word_cloud/word_cloud_main.js')]
         }
    # css = {'scss': [resource_string(__name__, 'css/word_cloud/display.scss')]}
    js_module_name = "WordCloud"

    Number_of_top_words = 250

    def handle_ajax(self, dispatch, get):
        """Ajax handler.

        Args:
            dispatch: string request slug
            get: dict request get parameters

        Returns:
            json string
        """
        if dispatch == 'submit':

            # self.all_words[word] -= 1
            # FIXME: fix this, when xblock will support mutable types.
            # Now we use this hack.
            # speed issues
            temp_all_words = self.all_words
            temp_top_words = self.top_words

            if self.submitted:

                for word in self.student_words:
                    temp_all_words[word] -= 1

                    if word in temp_top_words:
                        temp_top_words -= 1

            else:
                self.submitted = True

            self.student_words = get['student_words']

            question_words = {}

            for word in self.student_words:
                temp_all_words[word] += 1

                if word in temp_top_words:
                    temp_top_words += 1
                else:
                    if temp_all_words[word] > top_low_border:
                        question_words[word] = temp_all_words[word]


            self.all_words = temp_all_words

            self.top_words = self.update_top_words(question_words, temp_top_words)


            return json.dumps({'student_words': self.student_words,
                               'top_words': self.top_words,
                               })
        elif dispatch == 'get_state':
            return json.dumps({'student_answers': self.student_answers,
                               'top_words': self.top_words
                               })
        else:  # return error message
            return json.dumps({'error': 'Unknown Command!'})


    def update_top_words(question_words, top_words):

        for word, number in question_words:
            for top_word, top_number in top_words[:]:
                if top_number < number:
                    del top_words[top_word]
                    top_words[word] - number
                    break

        return top_words

    def get_html(self):
        """Renders parameters to template."""
        params = {
                  'element_id': self.location.html_id(),
                  'element_class': self.location.category,
                  'ajax_url': self.system.ajax_url,
                  'configuration_json': json.dumps({}),
                  }
        self.content = self.system.render_template('word_cloud.html', params)
        return self.content


class WordCloudDescriptor(WordCloudFields, MakoModuleDescriptor, XmlDescriptor):
    _tag_name = 'word_cloud'

    module_class = WordCloudModule
    template_dir_name = 'word_cloud'
    stores_state = True

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        """Pull out the data into dictionary.

        Args:
            xml_object: xml from file.
            system: `system` object.

        Returns:
            (definition, children) - tuple

        """
        definition = {}
        children = []

        return (definition, children)

    def definition_to_xml(self, resource_fs):
        """Return an xml element representing to this definition."""
        xml_str = '<{tag_name} />'.format(tag_name=self._tag_name)
        xml_object = etree.fromstring(xml_str)
        xml_object.set('display_name', self.display_name)
        xml_object.set('num_inputs', self.num_inputs)

        return xml_object
