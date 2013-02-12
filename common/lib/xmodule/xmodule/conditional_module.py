"""Conditional module is the xmodule, which you can use for disabling
some xmodules by conditions.
"""

import json
import logging
from lxml import etree
from pkg_resources import resource_string

from xmodule.x_module import XModule
from xmodule.modulestore import Location
from xmodule.seq_module import SequenceDescriptor
from xblock.core import String, Scope
from xmodule.modulestore.exceptions import ItemNotFoundError

log = logging.getLogger('mitx.' + __name__)


class ConditionalModule(XModule):
    """
    Blocks child module from showing unless certain conditions are met.

    Example:

        <conditional sources="i4x://.../problem_1; i4x://.../problem_2" completed="True">
            <show sources="i4x://.../test_6; i4x://.../Avi_resources"/>
            <video url_name="secret_video" />
        </conditional>

        TODO string comparison
            multiple answer for every poll

    """

    js = {'coffee': [resource_string(__name__, 'js/src/javascript_loader.coffee'),
                     resource_string(__name__, 'js/src/conditional/display.coffee'),
                     resource_string(__name__, 'js/src/collapsible.coffee'),

                    ]}

    js_module_name = "Conditional"
    css = {'scss': [resource_string(__name__, 'css/capa/display.scss')]}

    contents = String(scope=Scope.content)

    # Map
    # key: <tag attribute in xml>
    # value: <name of module attribute>
    conditions_map = {
        'poll_answer': 'poll_answer',  # poll_question attr
        'compeleted': 'is_competed',  # capa_problem attr
        'voted': 'voted'  # poll_question attr
    }

    def _get_condition(self):
        # Get first valid condition.
        for xml_attr, attr_name in self.conditions_map.iteritems():
            xml_value = self.descriptor.xml_attributes.get(xml_attr)
            if xml_value:
                return xml_value, attr_name
        raise Exception('Error in conditional module: unknown condition "%s"'
            % xml_attr)

    def is_condition_satisfied(self):
        self.required_modules = [self.system.get_module(descriptor.location) for
            descriptor in self.descriptor.get_required_module_descriptors()]
        xml_value, attr_name = self._get_condition()

        if xml_value:
            for module in self.required_modules:
                if not hasattr(module, attr_name):
                    raise Exception('Error in conditional module: \
                        required module %s has no .is_completed() method'
                        % module)

                attr = getattr(module, attr_name)
                if callable(attr):
                    attr = attr()

                return xml_value == str(attr)
        return False

    def get_html(self):
        return self.system.render_template('conditional_ajax.html', {
            'element_id': self.location.html_id(),
            'id': self.id,
            'ajax_url': self.system.ajax_url,
            'passed': json.dumps(self.is_condition_satisfied())
        })

    def handle_ajax(self, dispatch, post):
        """This is called by courseware.moduleodule_render, to handle
        an AJAX call.
        """
        if not self.is_condition_satisfied():
            context = {'module': self,
                       'message': self.descriptor.xml_attributes.get('message')}
            html = self.system.render_template('conditional_module.html',
                context)
            return json.dumps({'html': [html], 'passed': False})

        if self.contents is None:
            self.contents = [self.system.get_module(child_descriptor.location
                ).get_html()
                for child_descriptor in self.descriptor.get_children()]

        html = self.contents
        return json.dumps({'html': html, 'passed': True})


class ConditionalDescriptor(SequenceDescriptor):
    """Descriptor for conditional xmodule."""
    module_class = ConditionalModule

    filename_extension = "xml"

    stores_state = True
    has_score = False

    def get_required_module_descriptors(self):
        """TODO: Returns a list of XModuleDescritpor instances upon which this module depends, but are
        not children of this module"""
        descriptors = []
        sources = self.xml_attributes.get('sources')
        if sources:
            locations = [location.strip() for location in sources.split(';')]
            for location in locations:
                # Check valid location url.
                if Location.is_valid(location):
                    try:
                        descriptor = self.system.load_item(location)
                        descriptors.append(descriptor)
                    except ItemNotFoundError:
                        log.exception("Invalid module by location.")
        return descriptors

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        def parse_show_tag(child):
            """Return list of valid module urls from <show> tag."""
            urls = []
            sources = child.get('sources')
            if sources:
                locations = [location.strip() for location in sources.split(';')]
                for location in locations:
                    # Check valid location url.
                    if Location.is_valid(location):
                        try:
                            system.load_item(location)
                            urls.append(location)
                        except ItemNotFoundError:
                            log.exception("Invalid descriptor by location.")
            return urls

        children = []
        for child in xml_object:
            if child.tag == 'show':
                children.extend(parse_show_tag(child))
            else:
                try:
                    descriptor = system.process_xml(etree.tostring(child))
                    module_url = descriptor.location.url()
                    children.append(module_url)
                except:
                    log.exception("Unable to load child when parsing Conditional.")
        return {}, children

    def definition_to_xml(self, resource_fs):
        xml_object = etree.Element('sequential')
        for child in self.get_children():
            xml_object.append(
                etree.fromstring(child.export_to_xml(resource_fs)))
        return xml_object
