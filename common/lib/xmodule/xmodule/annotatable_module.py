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

    def _set_annotation_class(self, el):
        """ Sets the CSS class on the annotation span. """

        cls = ['annotatable-span', 'highlight']
        cls.append('highlight-'+self._get_highlight(el))
        el.set('class', ' '.join(cls))

    def _set_annotation_data(self, el):
        """ Transforms the annotation span's xml attributes to HTML data attributes. """

        attrs_map = {'body': 'data-comment-body', 'title': 'data-comment-title'}
        for xml_key in attrs_map.keys():
            if xml_key in el.attrib:
                value = el.get(xml_key, '')
                html_key = attrs_map[xml_key]
                el.set(html_key, value)
                del el.attrib[xml_key]

    def _get_highlight(self, el):
        """ Returns the name of the marker/highlight color for the span if it is valid, otherwise none."""

        valid_highlights = ['yellow', 'orange', 'purple', 'blue', 'green']
        default_highlight = 'yellow'
        highlight = el.get('highlight', default_highlight)
        if highlight in valid_highlights:
            return highlight
        return default_highlight

    def _render_content(self):
        """ Renders annotatable content by transforming spans and adding discussions. """
        xmltree = etree.fromstring(self.content)
        xmltree.tag = 'div'

        for el in xmltree.findall('.//annotation'):
            el.tag = 'div'
            self._set_annotation_class(el)
            self._set_annotation_data(el)

        return etree.tostring(xmltree, encoding='unicode')

    def get_html(self):
        """ Renders parameters to template. """
        context = {
            'display_name': self.display_name,
            'element_id': self.element_id,
            'discussion_id': self.discussion_id,
            'content_html': self._render_content()
        }

        return self.system.render_template('annotatable.html', context)

    def __init__(self, system, location, definition, descriptor,
                 instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, descriptor,
                         instance_state, shared_state, **kwargs)

        xmltree = etree.fromstring(self.definition['data'])
        discussion_id = ''
        if 'discussion' in xmltree.attrib:
            discussion_id = xmltree.get('discussion')
            del xmltree.attrib['discussion']

        self.content = etree.tostring(xmltree, encoding='unicode')
        self.element_id = self.location.html_id()
        self.discussion_id = discussion_id

class AnnotatableDescriptor(RawDescriptor):
    module_class = AnnotatableModule
    stores_state = True
    template_dir_name = "annotatable"