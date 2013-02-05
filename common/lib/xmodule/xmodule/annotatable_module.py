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
        return element.tag == 'span' and element.get('class') == 'annotatable'

    def _is_span_container(self, element):
        """ Returns true if the element is a valid span contanier, false otherwise. """
        return element.tag == 'p' # Assume content is in paragraph form (for now...)

    def _iterspans(self, xmltree, callbacks):
        """ Iterates over span elements and invokes each callback on the span. """

        index = 0
        for element in xmltree.iter('span'):
            if self._is_span(element):
                for callback in callbacks:
                    callback(element, index, xmltree)
                index += 1
    
    def _get_span_container(self, span):
        """ Returns the first container element of the span.
            The intent is to add the discussion widgets at the 
            end of the container, not interspersed with the text. """

        container = None
        for parent in span.iterancestors():
            if self._is_span_container(parent):
                container = parent
                break 
       
        if container is None:
            return parent
        return container

    def _get_discussion_html(self, discussion_id, discussion_title):
        """ Returns html to display the discussion thread """
        context = {
                   'discussion_id': discussion_id,
                   'discussion_title': discussion_title
        }
        return self.system.render_template('annotatable_discussion.html', context)
    
    def _attach_discussion(self, span, index, xmltree):
        """ Attaches a discussion thread to the annotation span. """

        span_id = 'span-{0}'.format(index) # How should we anchor spans? 
        span.set('data-span-id', span_id)

        discussion_id = 'discussion-{0}'.format(index) # How do we get a real discussion ID?
        discussion_title = 'Thread Title {0}'.format(index) # How do we get the discussion Title?
        discussion_html = self._get_discussion_html(discussion_id, discussion_title)
        discussion_xmltree = etree.fromstring(discussion_html)

        span_container = self._get_span_container(span)
        span_container.append(discussion_xmltree)

        self.discussion_for[span_id] = discussion_id
    
    def _add_icon(self, span, index, xmltree):
        """ Adds an icon to the annotation span. """

        span_icon = etree.Element('span', { 'class': 'annotatable-icon'} )
        span_icon.text = '';
        span_icon.tail = span.text
        span.text = ''
        span.insert(0, span_icon)
    
    def _render(self):
        """ Renders annotatable content by transforming spans and adding discussions. """

        xmltree = etree.fromstring(self.content)
        self._iterspans(xmltree, [ self._add_icon, self._attach_discussion ])
        return etree.tostring(xmltree)

    def get_html(self):
        """ Renders parameters to template. """
        
        context = {
            'display_name': self.display_name,
            'element_id': self.element_id,
            'html_content': self._render(),
            'json_discussion_for': json.dumps(self.discussion_for)        
        }

        # template dir: lms/templates
        return self.system.render_template('annotatable.html', context)

    def __init__(self, system, location, definition, descriptor,
                 instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, descriptor,
                         instance_state, shared_state, **kwargs)
        
        self.element_id = self.location.html_id();
        self.content = self.definition['data']
        self.discussion_for = {} # Maps spans to discussions by id (for JS)


class AnnotatableDescriptor(RawDescriptor):
    module_class = AnnotatableModule
    stores_state = True
    template_dir_name = "annotatable"
