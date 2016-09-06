"""Conditional module is the xmodule, which you can use for disabling
some xmodules by conditions.
"""

import json
import logging
from lazy import lazy
from lxml import etree
from pkg_resources import resource_string

from xmodule.x_module import XModule, STUDENT_VIEW
from xmodule.seq_module import SequenceDescriptor
from xblock.fields import Scope, ReferenceList
from xmodule.modulestore.exceptions import ItemNotFoundError


log = logging.getLogger('edx.' + __name__)


class ConditionalFields(object):
    has_children = True
    show_tag_list = ReferenceList(help="List of urls of children that are references to external modules", scope=Scope.content)
    sources_list = ReferenceList(help="List of sources upon which this module is conditional", scope=Scope.content)


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

    js = {
        'coffee': [
            resource_string(__name__, 'js/src/javascript_loader.coffee'),
            resource_string(__name__, 'js/src/conditional/display.coffee'),
        ],
        'js': [
            resource_string(__name__, 'js/src/collapsible.js'),
        ]
    }

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
        raise Exception(
            'Error in conditional module: no known conditional found in {!r}'.format(
                self.descriptor.xml_attributes.keys()
            )
        )

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

        html = [child.render(STUDENT_VIEW).content for child in self.get_display_items()]

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

    resources_dir = None

    filename_extension = "xml"

    has_score = False

    show_in_read_only_mode = True

    def __init__(self, *args, **kwargs):
        """
        Create an instance of the conditional module.
        """
        super(ConditionalDescriptor, self).__init__(*args, **kwargs)
        # Convert sources xml_attribute to a ReferenceList field type so Location/Locator
        # substitution can be done.
        if not self.sources_list:
            if 'sources' in self.xml_attributes and isinstance(self.xml_attributes['sources'], basestring):
                self.sources_list = [
                    self.location.course_key.make_usage_key_from_deprecated_string(item)
                    for item in ConditionalDescriptor.parse_sources(self.xml_attributes)
                ]

    @staticmethod
    def parse_sources(xml_element):
        """ Parse xml_element 'sources' attr and return a list of location strings. """
        sources = xml_element.get('sources')
        if sources:
            return [location.strip() for location in sources.split(';')]

    def get_required_module_descriptors(self):
        """Returns a list of XModuleDescriptor instances upon
        which this module depends.
        """
        descriptors = []
        for location in self.sources_list:
            try:
                descriptor = self.system.load_item(location)
                descriptors.append(descriptor)
            except ItemNotFoundError:
                msg = "Invalid module by location."
                log.exception(msg)
                self.system.error_tracker(msg)

        return descriptors

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        children = []
        show_tag_list = []
        for child in xml_object:
            if child.tag == 'show':
                locations = ConditionalDescriptor.parse_sources(child)
                for location in locations:
                    children.append(location)
                    show_tag_list.append(location)
            else:
                try:
                    descriptor = system.process_xml(etree.tostring(child))
                    children.append(descriptor.scope_ids.usage_id)
                except:
                    msg = "Unable to load child when parsing Conditional."
                    log.exception(msg)
                    system.error_tracker(msg)
        return {'show_tag_list': show_tag_list}, children

    def definition_to_xml(self, resource_fs):
        xml_object = etree.Element(self._tag_name)
        for child in self.get_children():
            if child.location not in self.show_tag_list:
                self.runtime.add_block_as_child_node(child, xml_object)

        if self.show_tag_list:
            show_str = u'<{tag_name} sources="{sources}" />'.format(
                tag_name='show', sources=';'.join(location.to_deprecated_string() for location in self.show_tag_list))
            xml_object.append(etree.fromstring(show_str))

        # Overwrite the original sources attribute with the value from sources_list, as
        # Locations may have been changed to Locators.
        stringified_sources_list = map(lambda loc: loc.to_deprecated_string(), self.sources_list)
        self.xml_attributes['sources'] = ';'.join(stringified_sources_list)
        return xml_object
