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
from xblock.core import String, Scope, List
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
        'completed': 'is_completed',  # capa_problem attr
        'attempted': 'is_attempted',  # capa_problem attr
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
        self.required_modules = [self.system.get_module(descriptor) for
            descriptor in self.descriptor.get_required_module_descriptors()]

        xml_value, attr_name = self._get_condition()

        if xml_value and self.required_modules:
            for module in self.required_modules:
                if not hasattr(module, attr_name):
                    raise Exception('Error in conditional module: \
                    required module {module} has no {module_attr}'.format(
                        module=module, module_attr=attr_name))

                attr = getattr(module, attr_name)
                if callable(attr):
                    attr = attr()

                if xml_value != str(attr):
                    break
            else:
                return True
        return False

    def get_html(self):
        # Calculate html ids of dependencies
        self.required_html_ids = [descriptor.location.html_id() for
            descriptor in self.descriptor.get_required_module_descriptors()]

        return self.system.render_template('conditional_ajax.html', {
            'element_id': self.location.html_id(),
            'id': self.id,
            'ajax_url': self.system.ajax_url,
            'depends': ';'.join(self.required_html_ids)
        })

    def handle_ajax(self, dispatch, post):
        """This is called by courseware.moduleodule_render, to handle
        an AJAX call.
        """
        if not self.is_condition_satisfied():
            message = self.descriptor.xml_attributes.get('message')
            context = {'module': self,
                       'message': message}
            html = self.system.render_template('conditional_module.html',
                context)
            return json.dumps({'html': [html], 'passed': False,
                                'message': bool(message)})

        if self.contents is None:
            self.contents = [self.system.get_module(child_descriptor).get_html()
                    for child_descriptor in self.descriptor.get_children()]

        html = self.contents
        return json.dumps({'html': html, 'passed': True})


class ConditionalDescriptor(SequenceDescriptor):
    """Descriptor for conditional xmodule."""
    _tag_name = 'conditional'

    module_class = ConditionalModule

    filename_extension = "xml"

    stores_state = True
    has_score = False

    show_tag_list = List(help="Poll answers", scope=Scope.content)

    @staticmethod
    def parse_sources(xml_element, system, return_descriptor=False):
        """Parse xml_element 'sources' attr and:
        if return_descriptor=True - return list of descriptors
        if return_descriptor=False - return list of locations
        """
        result = []
        sources = xml_element.get('sources')
        if sources:
            locations = [location.strip() for location in sources.split(';')]
            for location in locations:
                # Check valid location url.
                if Location.is_valid(location):
                    try:
                        descriptor = system.load_item(location)
                        if return_descriptor:
                            result.append(descriptor)
                        else:
                            result.append(location)
                    except ItemNotFoundError:
                        log.exception("Invalid module by location.")
        return result

    def get_required_module_descriptors(self):
        """Returns a list of XModuleDescritpor instances upon
        which this module depends.
        """
        return ConditionalDescriptor.parse_sources(
            self.xml_attributes, self.system, True)

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        children = []
        show_tag_list = []
        for child in xml_object:
            if child.tag == 'show':
                location = ConditionalDescriptor.parse_sources(
                    child, system)
                children.extend(location)
                show_tag_list.extend(location)
            else:
                try:
                    descriptor = system.process_xml(etree.tostring(child))
                    module_url = descriptor.location.url()
                    children.append(module_url)
                except:
                    log.exception("Unable to load child when parsing Conditional.")
        return {'show_tag_list': show_tag_list}, children

    def definition_to_xml(self, resource_fs):
        xml_object = etree.Element(self._tag_name)
        for child in self.get_children():
            location = str(child.location)
            if location in self.show_tag_list:
                show_str = '<{tag_name} sources="{sources}" />'.format(
                    tag_name='show', sources=location)
                xml_object.append(etree.fromstring(show_str))
            else:
                xml_object.append(
                    etree.fromstring(child.export_to_xml(resource_fs)))
        return xml_object
