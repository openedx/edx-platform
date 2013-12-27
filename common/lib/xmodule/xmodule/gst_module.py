"""
Graphical slider tool module is ungraded xmodule used by students to
understand functional dependencies.
"""

import json
import logging
from lxml import etree
from lxml import html
import xmltodict

from xmodule.editing_module import XMLEditingDescriptor
from xmodule.xml_module import XmlDescriptor
from xmodule.x_module import XModule
from xmodule.stringify import stringify_children
from pkg_resources import resource_string
from xblock.fields import String, Scope

log = logging.getLogger(__name__)

DEFAULT_RENDER = """
    <h2>Graphic slider tool: Dynamic range and implicit functions.</h2>

    <p>You can make the range of the x axis (but not ticks of x axis) of
      functions depend on a parameter value. This can be useful when the
      function domain needs to be variable.</p>
    <p>Implicit functions like a circle can be plotted as 2 separate
        functions of the same color.</p>
     <div style="height:50px;">
     <slider var='r' style="width:400px;float:left;"/>
     <textbox var='r' style="float:left;width:60px;margin-left:15px;"/>
   </div>
    <plot style="margin-top:15px;margin-bottom:15px;"/>
"""

DEFAULT_CONFIGURATION = """
    <parameters>
        <param var="r" min="5" max="25" step="0.5" initial="12.5" />
    </parameters>
    <functions>
      <function color="red">Math.sqrt(r * r - x * x)</function>
      <function color="red">-Math.sqrt(r * r - x * x)</function>
      <function color="red">Math.sqrt(r * r / 20 - Math.pow(x-r/2.5, 2)) + r/8</function>
      <function color="red">-Math.sqrt(r * r / 20 - Math.pow(x-r/2.5, 2)) + r/5.5</function>
      <function color="red">Math.sqrt(r * r / 20 - Math.pow(x+r/2.5, 2)) + r/8</function>
      <function color="red">-Math.sqrt(r * r / 20 - Math.pow(x+r/2.5, 2)) + r/5.5</function>
      <function color="red">-Math.sqrt(r * r / 5 - x * x) - r/5.5</function>
    </functions>
    <plot>
      <xrange>
        <!-- dynamic range -->
          <min>-r</min>
          <max>r</max>
      </xrange>
      <num_points>1000</num_points>
      <xticks>-30, 6, 30</xticks>
      <yticks>-30, 6, 30</yticks>
    </plot>
"""


class GraphicalSliderToolFields(object):
    data = String(
        help="Html contents to display for this module",
        default='<render>{}</render><configuration>{}</configuration>'.format(
            DEFAULT_RENDER, DEFAULT_CONFIGURATION),
        scope=Scope.content
    )


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
            resource_string(__name__, 'js/src/graphical_slider_tool/general_methods.js'),
            resource_string(__name__, 'js/src/graphical_slider_tool/sliders.js'),
            resource_string(__name__, 'js/src/graphical_slider_tool/inputs.js'),
            resource_string(__name__, 'js/src/graphical_slider_tool/graph.js'),
            resource_string(__name__, 'js/src/graphical_slider_tool/el_output.js'),
            resource_string(__name__, 'js/src/graphical_slider_tool/g_label_el_output.js'),
            resource_string(__name__, 'js/src/graphical_slider_tool/gst.js')
        ]
    }
    css = {'scss': [resource_string(__name__, 'css/gst/display.scss')]}
    js_module_name = "GraphicalSliderTool"

    @property
    def configuration(self):
        return stringify_children(
            html.fromstring(self.data).xpath('configuration')[0]
        )

    @property
    def render(self):
        return stringify_children(
            html.fromstring(self.data).xpath('render')[0]
        )

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
            'graphical_slider_tool.html', params
        )
        return content

    def substitute_controls(self, html_string):
        """ Substitutes control elements (slider, textbox and plot) in
        html_string with their divs. Html_string is content of <render> tag
        inside <graphical_slider_tool> tag. Documentation on how information in
        <render> tag is organized and processed is located in:
        edx-platform/docs/build/html/graphical_slider_tool.html.

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
                plot_div.format(
                    element_class=self.html_class,
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
                slider_div.format(
                    element_class=self.html_class,
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
                input_div.format(
                    element_class=self.html_class,
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
        root = '<root class="{}">{}</root>'.format(
            self.html_class,
            self.configuration)
        return json.dumps(xmltodict.parse(root))


class GraphicalSliderToolDescriptor(GraphicalSliderToolFields, XMLEditingDescriptor, XmlDescriptor):
    module_class = GraphicalSliderToolModule

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
                raise ValueError(u"Graphical Slider Tool definition must include \
                    exactly one '{0}' tag".format(child))

        expected_children_level_1 = ['functions']
        for child in expected_children_level_1:
            if len(xml_object.xpath('configuration')[0].xpath(child)) != 1:
                raise ValueError(u"Graphical Slider Tool definition must include \
                    exactly one '{0}' tag".format(child))
        # finished

        return {
            'data': stringify_children(xml_object)
        }, []

    def definition_to_xml(self, resource_fs):
        '''Return an xml element representing this definition.'''
        data = u'<{tag}>{body}</{tag}>'.format(
            tag='graphical_slider_tool',
            body=self.data)
        xml_object = etree.fromstring(data)
        return xml_object
