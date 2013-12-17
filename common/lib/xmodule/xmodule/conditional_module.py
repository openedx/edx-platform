"""Conditional module is the xmodule, which you can use for disabling
some xmodules by conditions.
"""

import json
import logging
from lazy import lazy
from lxml import etree
from pkg_resources import resource_string

from xmodule.x_module import XModule
from xmodule.modulestore import Location
from xmodule.seq_module import SequenceDescriptor
from xblock.fields import Scope, List
from xmodule.modulestore.exceptions import ItemNotFoundError


log = logging.getLogger('edx.' + __name__)


class ConditionalFields(object):
    has_children = True
    show_tag_list = List(help="Poll answers", scope=Scope.content)


class ConditionalModule(ConditionalFields, XModule):
    """
    Blocks child module from showing unless certain conditions are met.

    Example:

        <conditional sources="i4x://.../problem_1; i4x://.../problem_2" completed="True">
            <show sources="i4x://.../test_6; i4x://.../Avi_resources"/>
            <video url_name="secret_video" />
        </conditional>

        <conditional> tag attributes:
            sources - location id of required modules, separated by ';'

            submitted - map to `is_submitted` module method.
            (pressing RESET button makes this function to return False.)

            attempted - map to `is_attempted` module method
            correct - map to `is_correct` module method
            poll_answer - map to `poll_answer` module attribute
            voted - map to `voted` module attribute

        <show> tag attributes:
            sources - location id of required modules, separated by ';'

        You can add you own rules for <conditional> tag, like
        "completed", "attempted" etc. To do that yo must extend
        `ConditionalModule.conditions_map` variable and add pair:
            my_attr: my_property/my_method

        After that you can use it:
            <conditional my_attr="some value" ...>
                ...
            </conditional>

        And my_property/my_method will be called for required modules.

    """

    js = {'coffee': [resource_string(__name__, 'js/src/javascript_loader.coffee'),
                     resource_string(__name__, 'js/src/conditional/display.coffee'),
                     resource_string(__name__, 'js/src/collapsible.coffee'),
                     ]}

    js_module_name = "Conditional"
    css = {'scss': [resource_string(__name__, 'css/capa/display.scss')]}

    # Map
    # key: <tag attribute in xml>
    # value: <name of module attribute>
    conditions_map = {
        'poll_answer': 'poll_answer',  # poll_question attr

        # problem was submitted (it can be wrong)
        # if student will press reset button after that,
        # state will be reverted
        'submitted': 'is_submitted',  # capa_problem attr

        # if student attempted problem
        'attempted': 'is_attempted',  # capa_problem attr

        # if problem is full points
        'correct': 'is_correct',

        'voted': 'voted'  # poll_question attr
    }

    def _get_condition(self):
        # Get first valid condition.
        for xml_attr, attr_name in self.conditions_map.iteritems():
            xml_value = self.descriptor.xml_attributes.get(xml_attr)
            if xml_value:
                return xml_value, attr_name
        raise Exception('Error in conditional module: unknown condition "%s"' % xml_attr)

    @lazy
    def required_modules(self):
        return [self.system.get_module(descriptor) for
                descriptor in self.descriptor.get_required_module_descriptors()]

    def is_condition_satisfied(self):
        xml_value, attr_name = self._get_condition()

        if xml_value and self.required_modules:
            for module in self.required_modules:
                if not hasattr(module, attr_name):
                    # We don't throw an exception here because it is possible for
                    # the descriptor of a required module to have a property but
                    # for the resulting module to be a (flavor of) ErrorModule.
                    # So just log and return false.
                    log.warn('Error in conditional module: \
                        required module {module} has no {module_attr}'.format(module=module, module_attr=attr_name))
                    return False

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

    def handle_ajax(self, _dispatch, _data):
        """This is called by courseware.moduleodule_render, to handle
        an AJAX call.
        """
        if not self.is_condition_satisfied():
            defmsg = "{link} must be attempted before this will become visible."
            message = self.descriptor.xml_attributes.get('message', defmsg)
            context = {'module': self,
                       'message': message}
            html = self.system.render_template('conditional_module.html',
                                               context)
            return json.dumps({'html': [html], 'message': bool(message)})

        html = [child.render('student_view').content for child in self.get_display_items()]

        return json.dumps({'html': html})

    def get_icon_class(self):
        new_class = 'other'
        # HACK: This shouldn't be hard-coded to two types
        # OBSOLETE: This obsoletes 'type'
        class_priority = ['video', 'problem']

        child_classes = [self.system.get_module(child_descriptor).get_icon_class()
                         for child_descriptor in self.descriptor.get_children()]
        for c in class_priority:
            if c in child_classes:
                new_class = c
        return new_class


class ConditionalDescriptor(ConditionalFields, SequenceDescriptor):
    """Descriptor for conditional xmodule."""
    _tag_name = 'conditional'

    module_class = ConditionalModule

    filename_extension = "xml"

    has_score = False

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
                if Location.is_valid(location):  # Check valid location url.
                    try:
                        if return_descriptor:
                            descriptor = system.load_item(location)
                            result.append(descriptor)
                        else:
                            result.append(location)
                    except ItemNotFoundError:
                        msg = "Invalid module by location."
                        log.exception(msg)
                        system.error_tracker(msg)
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
                    msg = "Unable to load child when parsing Conditional."
                    log.exception(msg)
                    system.error_tracker(msg)
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
