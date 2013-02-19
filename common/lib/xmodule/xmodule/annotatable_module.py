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

        problem_el = span.find('problem')
        if problem_el is not None:
            problem_id = str(index + 1)
            problem_el.set('problem_id', problem_id)
            span.set('data-problem-id', problem_id)
            parsed_problem = self._parse_problem(problem_el)
            parsed_problem['discussion_id'] = span.get('data-discussion-id')
            if parsed_problem is not None:
                self.problems.append(parsed_problem)
            span.remove(problem_el)

    def _parse_problem(self, problem_el):
        """ Returns the problem XML as a dict. """
        prompt_el = problem_el.find('prompt')
        answer_el = problem_el.find('answer')
        tags_el = problem_el.find('tags')

        if any(v is None for v in (prompt_el, answer_el, tags_el)):
            return None

        tags = []
        for tag_el in tags_el.iterchildren('tag'):
            tags.append({
                'name': tag_el.get('name', ''),
                'display_name': tag_el.get('display_name', ''),
                'weight': tag_el.get('weight', 0),
                'answer': tag_el.get('answer', 'n') == 'y'
            })

        result = {
            'problem_id': problem_el.get('problem_id'),
            'prompt': prompt_el.text, 
            'answer': answer_el.text,
            'tags': tags
        }

        return result

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

    def _render_items(self):
        items = []

        if self.render_as_problems:
            discussions = {}
            for child in self.get_display_items():
                discussions[child.discussion_id] = child.get_html()

            for problem in self.problems:
                discussion = None
                discussion_id = problem['discussion_id']
                if discussion_id in discussions:
                    discussion = {
                        'discussion_id': discussion_id,
                        'content': discussions[discussion_id]
                    }
                items.append({
                    'problem': problem,
                    'discussion': discussion
                })
        else:
            for child in self.get_display_items():
                items.append({ 'discussion': {
                    'discussion_id': child.discussion_id,
                    'content': child.get_html()
                }})

        return items

    def get_html(self):
        """ Renders parameters to template. """

        html_content = self._render_content()
        items = self._render_items()

        context = {
            'display_name': self.display_name,
            'problem_name': self.problem_name,
            'element_id': self.element_id,
            'html_content': html_content,
            'render_as_problems': self.render_as_problems,
            'items': items
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
        self.render_as_problems = (self.problem_type == 'classification')
        self.problem_name = self._get_problem_name(self.problem_type)
        self.problems = []


class AnnotatableDescriptor(RawDescriptor):
    module_class = AnnotatableModule
    stores_state = True
    template_dir_name = "annotatable"


    @classmethod
    def definition_from_xml(cls, xml_object, system):
        children = []
        for child in xml_object.findall('discussion'):
            try:
                children.append(system.process_xml(etree.tostring(child, encoding='unicode')).location.url())
                xml_object.remove(child)
            except Exception as e:
                log.exception("Unable to load child when parsing Sequence. Continuing...")
                if system.error_tracker is not None:
                    system.error_tracker("ERROR: " + str(e))
                continue
        return {
            'data': etree.tostring(xml_object, pretty_print=True, encoding='unicode'),
            'children': children
        }

    def definition_to_xml(self, resource_fs):
        try:
            root = etree.fromstring(self.definition['data'])
            for child in self.get_children():
                root.append(etree.fromstring(child.export_to_xml(resource_fs)))
            return root
        except etree.XMLSyntaxError as err:
            # Can't recover here, so just add some info and
            # re-raise
            lines = self.definition['data'].split('\n')
            line, offset = err.position
            msg = ("Unable to create xml for problem {loc}. "
                   "Context: '{context}'".format(
                context=lines[line - 1][offset - 40:offset + 40],
                loc=self.location))
            raise Exception, msg, sys.exc_info()[2]