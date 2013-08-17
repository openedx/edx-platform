"""
Graphical slider tool module is ungraded xmodule used by students to
understand functional dependencies.
"""

import json
import logging
from lxml import etree
from lxml import html
import xmltodict

from xmodule.mako_module import MakoModuleDescriptor
from xmodule.xml_module import XmlDescriptor
from xmodule.x_module import XModule
from xmodule.stringify import stringify_children
from pkg_resources import resource_string
from xblock.core import String, Scope


log = logging.getLogger(__name__)


class GraphicalSliderToolFields(object):
    render = String(scope=Scope.content)
    configuration = String(scope=Scope.content)


class GraphicalSliderToolModule(GraphicalSliderToolFields, XModule):
    ''' Graphical-Slider-Tool Module
    '''

    js = {
      'coffee': [resource_string(__name__, 'js/src/javascript_loader.coffee')],
      'js': [
        # 3rd party libraries used by graphic slider tool.
        # TODO - where to store them - outside xmodule?
        resource_string(__name__, 'js/src/graphical_slider_tool/gst_main.js'),
        resource_string(__name__, 'js/src/graphical_slider_tool/state.js'),
        resource_string(__name__, 'js/src/graphical_slider_tool/logme.js'),
        resource_string(__name__, 'js/src/graphical_slider_tool/general_methods.js'),
        resource_string(__name__, 'js/src/graphical_slider_tool/sliders.js'),
        resource_string(__name__, 'js/src/graphical_slider_tool/inputs.js'),
        resource_string(__name__, 'js/src/graphical_slider_tool/graph.js'),
        resource_string(__name__, 'js/src/graphical_slider_tool/el_output.js'),
        resource_string(__name__, 'js/src/graphical_slider_tool/g_label_el_output.js'),
        resource_string(__name__, 'js/src/graphical_slider_tool/gst.js')

      ]
    }
    js_module_name = "GraphicalSliderTool"

    def get_html(self):
        """ Renders parameters to template. """

        # these 3 will be used in class methods
        self.html_id = self.location.html_id()
        self.html_class = self.location.category
        self.configuration_json = self.build_configuration_json()
        params = {
                  'gst_html': self.substitute_controls(self.render),
                  'element_id': self.html_id,
                  'element_class': self.html_class,
                  'configuration_json': self.configuration_json
                  }
        content = self.system.render_template(
                        'graphical_slider_tool.html', params)
        return content

    def substitute_controls(self, html_string):
        """ Substitutes control elements (slider, textbox and plot) in
        html_string with their divs. Html_string is content of <render> tag
        inside <graphical_slider_tool> tag. Documentation on how information in
        <render> tag is organized and processed is located in:
        mitx/docs/build/html/graphical_slider_tool.html.

        Args:
            html_string: content of <render> tag, with controls as xml tags,
                         e.g. <slider var="a"/>.

        Returns:
                html_string with control tags replaced by proper divs
                (<slider var="a"/> -> <div class="....slider" > </div>)
        """

        xml = html.fromstring(html_string)

        # substitute plot, if presented
        plot_div = '<div class="{element_class}_plot" id="{element_id}_plot" \
                    style="{style}"></div>'
        plot_el = xml.xpath('//plot')
        if plot_el:
            plot_el = plot_el[0]
            plot_el.getparent().replace(plot_el, html.fromstring(
                                plot_div.format(element_class=self.html_class,
                                               element_id=self.html_id,
                                               style=plot_el.get('style', ""))))

        # substitute sliders
        slider_div = '<div class="{element_class}_slider" \
                                   id="{element_id}_slider_{var}" \
                                   data-var="{var}" \
                                   style="{style}">\
                     </div>'
        slider_els = xml.xpath('//slider')
        for slider_el in slider_els:
            slider_el.getparent().replace(slider_el, html.fromstring(
                                slider_div.format(element_class=self.html_class,
                                    element_id=self.html_id,
                                    var=slider_el.get('var', ""),
                                    style=slider_el.get('style', ""))))

        # substitute inputs aka textboxes
        input_div = '<input class="{element_class}_input" \
                                  id="{element_id}_input_{var}_{input_index}" \
                                   data-var="{var}" style="{style}"/>'
        input_els = xml.xpath('//textbox')
        for input_index, input_el in enumerate(input_els):
            input_el.getparent().replace(input_el, html.fromstring(
                                input_div.format(element_class=self.html_class,
                                        element_id=self.html_id,
                                        var=input_el.get('var', ""),
                                        style=input_el.get('style', ""),
                                        input_index=input_index)))

        return html.tostring(xml)

    def build_configuration_json(self):
        """Creates json element from xml element (with aim to transfer later
         directly to javascript via hidden field in template). Steps:

            1. Convert xml tree to python dict.

            2. Dump dict to json.

        """
        # <root> added for interface compatibility with xmltodict.parse
        # class added for javascript's part purposes
        return json.dumps(xmltodict.parse('<root class="' + self.html_class +
                '">' + self.configuration + '</root>'))


class GraphicalSliderToolDescriptor(GraphicalSliderToolFields, MakoModuleDescriptor, XmlDescriptor):
    module_class = GraphicalSliderToolModule
    template_dir_name = 'graphical_slider_tool'

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
        expected_children_level_0 = ['render', 'configuration']
        for child in expected_children_level_0:
            if len(xml_object.xpath(child)) != 1:
                raise ValueError("Graphical Slider Tool definition must include \
                    exactly one '{0}' tag".format(child))

        expected_children_level_1 = ['functions']
        for child in expected_children_level_1:
            if len(xml_object.xpath('configuration')[0].xpath(child)) != 1:
                raise ValueError("Graphical Slider Tool definition must include \
                    exactly one '{0}' tag".format(child))
        # finished

        def parse(k):
            """Assumes that xml_object has child k"""
            return stringify_children(xml_object.xpath(k)[0])
        return {
                    'render': parse('render'),
                    'configuration': parse('configuration')
                }, []

    def definition_to_xml(self, resource_fs):
        '''Return an xml element representing this definition.'''
        xml_object = etree.Element('graphical_slider_tool')

        def add_child(k):
            child_str = '<{tag}>{body}</{tag}>'.format(tag=k, body=getattr(self, k))
            child_node = etree.fromstring(child_str)
            xml_object.append(child_node)

        for child in ['render', 'configuration']:
            add_child(child)

        return xml_object
