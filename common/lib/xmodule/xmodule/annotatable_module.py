import pprint
import json
import logging
import re

from lxml import etree
from pkg_resources import resource_string, resource_listdir

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from xmodule.modulestore.mongo import MongoModuleStore
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.content import StaticContent

import datetime
import time

log = logging.getLogger(__name__)

class AnnotatableModule(XModule):
    # Note: js and css in common/lib/xmodule/xmodule
    js = {'coffee': [resource_string(__name__, 'js/src/javascript_loader.coffee'),
                     resource_string(__name__, 'js/src/collapsible.coffee'),
                     resource_string(__name__, 'js/src/html/display.coffee'),
                     resource_string(__name__, 'js/src/annotatable/display.coffee')],
          'js': []
         }
    js_module_name = "Annotatable"
    css = {'scss': [resource_string(__name__, 'css/annotatable/display.scss')]}
    icon_class = 'annotatable'

    def _is_span(self, element):
        """ Returns true if the element is a valid annotation span, false otherwise. """
        return element.get('class') == 'annotatable'

    def _iterspans(self, xmltree, callbacks):
        """ Iterates over elements and invokes each callback on the span. """

        index = 0
        for element in xmltree.iter():
            if self._is_span(element):
                for callback in callbacks:
                    callback(element, index, xmltree)
                index += 1
 
    def _set_span_highlight(self, span, index, xmltree):
        """ Adds a highlight class to the span. """

        cls = ['annotatable-span', 'highlight']
        marker = self._get_marker_color(span)
        if marker is not None:
            cls.append('highlight-'+marker)

        span.set('class', ' '.join(cls))
        span.tag = 'div'
        
    def _set_span_comment(self, span, index, xmltree):
        """ Sets the comment class. """

        comment = span.find('comment')
        if comment is not None:
            comment.tag = 'div'
            comment.set('class', 'annotatable-comment')

    def _set_span_discussion(self, span, index, xmltree):
        """ Sets the associated discussion id for the span. """

        if 'discussion' in span.attrib:
            discussion = span.get('discussion')
            span.set('data-discussion-id', discussion)
            del span.attrib['discussion']

    def _set_problem(self, span, index, xmltree):
        """ Sets the associated problem. """

        problem = span.find('problem')
        if problem is not None:
            problem_id = str(index + 1)
            problem.set('problem_id', problem_id)
            span.set('data-problem-id', problem_id)
            parsed_problem = self._parse_problem(problem) 
            if parsed_problem is not None:
                self.problems.append(parsed_problem)

    def _parse_problem(self, problem):
        prompt_el = problem.find('prompt')
        answer_el = problem.find('answer')
        tags_el = problem.find('tags')

        tags = []
        for tag_el in tags_el.iterchildren('tag'):
            tags.append({
                'name': tag_el.get('name', ''),
                'display_name': tag_el.get('display_name', ''),
                'weight': tag_el.get('weight', 0),
                'answer': tag_el.get('answer', 'n') == 'y'
            })

        parsed = {
            'problem_id': problem.get('problem_id'),
            'prompt': prompt_el.text, 
            'answer': answer_el.text,
            'tags': tags
        }

        log.debug('parsed problem id = ' + parsed['problem_id'])
        log.debug("problem keys: " + ", ".join(parsed.keys()))
        log.debug('prompt = ' + parsed['prompt'])
        log.debug('answer = ' + parsed['answer'])
        log.debug('num tags = ' + str(len(parsed['tags'])))

        return parsed

    def _get_marker_color(self, span):
        """ Returns the name of the marker/highlight color for the span if it is valid, otherwise none."""

        valid_markers = ['yellow', 'orange', 'purple', 'blue', 'green']
        if 'marker' in span.attrib:
            marker = span.attrib['marker']
            del span.attrib['marker']
            if marker in valid_markers:
                return marker
        return None

    def _get_problem_name(self, problem_type):
        """ Returns the display name for the problem type. Defaults to annotated reading if none given. """
        problem_types = { 
            'classification':    'Classification Exercise + Guided Discussion',
            'annotated_reading': 'Annotated Reading + Guided Discussion'
        }

        if problem_type is not None and problem_type in problem_types.keys():
            return problem_types[problem_type]
        return problem_types['annotated_reading']


    def _render_content(self):
        """ Renders annotatable content by transforming spans and adding discussions. """

        callbacks = [   
            self._set_span_highlight,
            self._set_span_comment,
            self._set_span_discussion,
            self._set_problem
        ]

        xmltree = etree.fromstring(self.content)
        xmltree.tag = 'div'

        self._iterspans(xmltree, callbacks)

        return etree.tostring(xmltree)

    def get_html(self):
        """ Renders parameters to template. """
        
        context = {
            'display_name': self.display_name,
            'problem_name': self.problem_name,
            'element_id': self.element_id,
            'html_content': self._render_content(),
            'has_problems': self.has_problems,
            'problems': self.problems
        }

        return self.system.render_template('annotatable.html', context)

    def __init__(self, system, location, definition, descriptor,
                 instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, descriptor,
                         instance_state, shared_state, **kwargs)

        xmltree = etree.fromstring(self.definition['data'])

        self.element_id = self.location.html_id();
        self.content = self.definition['data']
        self.problem_type = xmltree.get('problem_type')
        self.has_problems = (self.problem_type == 'classification')
        self.problem_name = self._get_problem_name(self.problem_type)
        self.problems = []


class AnnotatableDescriptor(RawDescriptor):
    module_class = AnnotatableModule
    stores_state = True
    template_dir_name = "annotatable"
