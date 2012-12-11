"""
Graphical slider tool module is ungraded xmodule used by students to
understand functional dependencies.
"""

import json
import logging
from lxml import etree
import xmltodict
import re

from xmodule.mako_module import MakoModuleDescriptor
from xmodule.xml_module import XmlDescriptor
from xmodule.x_module import XModule
from xmodule.stringify import stringify_children
from pkg_resources import resource_string


log = logging.getLogger("mitx.common.lib.gst_module")


class GraphicalSliderToolModule(XModule):
    ''' Graphical-Slider-Tool Module
    '''

    js = {
      'js': [
        resource_string(__name__, 'js/src/graphical_slider_tool/gst_main.js'),
        resource_string(__name__, 'js/src/graphical_slider_tool/state.js'),
        resource_string(__name__, 'js/src/graphical_slider_tool/logme.js'),
        resource_string(__name__, 'js/src/graphical_slider_tool/general_methods.js'),
        resource_string(__name__, 'js/src/graphical_slider_tool/sliders.js'),
        resource_string(__name__, 'js/src/graphical_slider_tool/inputs.js'),
        resource_string(__name__, 'js/src/graphical_slider_tool/graph.js'),

        resource_string(__name__, 'js/src/graphical_slider_tool/gst.js')
      ]
    }
    js_module_name = "GraphicalSliderTool"

    def __init__(self, system, location, definition, descriptor, instance_state=None,
                 shared_state=None, **kwargs):
        """
        Definition  should have....
        sliders, text, module

        Sample file:

        <sequential>
          <vertical>
            <graphical_slider_tool>
              <render>
                <p>Graphic slider tool html.</p>
                <p>Can include 'input', 'slider' and 'plot' tags.
                They will be replaced by proper number, slider and plot
                widgets. </p>
                For example: $slider a$, second $slider b$,
                  number $input a$, and, plot:
                  $plot$

                  <!-- Sliders, and plot cannot be inside <p> -->
              </render>
              <configuration>
                <sliders>
                  <!-- optional: width=100 (in pixels), default is 400,
                  show_value=[editable, not-editable], default is disabled.-->
                  <slider var="a" range="-100, 1, 100" />
                  <slider var="b" range="-1000, 100, 1000" witdh="300"/>
                </sliders>
                <inputs>
                  <!-- optional: width=100 (in pixels), readonly=[true|false] -->
                  <input var="a" initial="1"/>
                </inputs>
                <plot>
                  <!-- optional: color=[standard web]; line=[true|false], default true;
                  dot=[true|false], default false; label="string",
                  style of line =[normal, dashed], default normal,
                  point size-->
                  <function y="x^2 + a" />
                  <function y="3*x + b" color="red"/>
                  <!-- asymtotes are functions,
                  optional: name="string" -->
                  <function y="b" color="red" style="dashed" name="b"/>
                  <function y="b/2" color="red" style="dashed" name="b/2"/>
                  <!-- xrange: min, max, yrange is calculated automatically -->
                  <xrange>-10, 10</xrange>
                  <!-- optional number of points, default is 300 -->
                  <numpoints>60</numpoints>
                  <!-- xticks and yticks are optional: min, step, max -->
                  <xticks>-9, 1, 9</xticks>
                  <yticks>-9, 1, 9</yticks>
                  <!-- xaxis and xaxis are optional -->
                  <xaxis unit="cm"/>
                  <yaxis unit="s"/>
                </plot>
                <!-- if some parameter in function is not related to any slider or
                number, then only error message is displayed.
                Sliders and numbers are optional. Plot is required.-->
              </configuration>
            </graphical_slider_tool>
          </vertical>
        </sequential>
        """
        XModule.__init__(self, system, location, definition, descriptor,
                         instance_state, shared_state, **kwargs)

    def get_html(self):
        self.get_configuration()
        self.html_id = self.location.html_id()
        self.html_class = self.location.category
        gst_html = self.substitute_controls(self.definition['render'].strip())
        # import ipdb; ipdb.set_trace()
        params = {
                  'gst_html': gst_html,
                  'element_id': self.html_id,
                  'element_class': self.html_class,
                  'configuration_json': self.configuration_json
                  }
        self.content = (self.system.render_template(
                        'graphical_slider_tool.html', params))
        # import ipdb; ipdb.set_trace()
        return self.content

    def substitute_controls(self, html_string):
        """ Substitue control element via their divs.
        Simple variant: slider and plot controls are not inside any tag.
        """
        #substitute plot
        plot_div = '<div class="' + self.html_class + '_plot" id="' + self.html_id + '_plot" \
        style="width: 600px; height: 600px; padding: 0px; position: relative;">This is plot</div>'
        html_string = html_string.replace('$plot$', plot_div)

        # substitute sliders
        sliders = json.loads(self.configuration_json)['root']['sliders']['slider']
        if type(sliders) == dict:
            sliders = [sliders]
        vars = [x['@var'] for x in sliders]

        slider_div = '<span class="{element_class}_slider" id="{element_id}_slider_{var}" \
        data-var="{var}"></span>'

        for var in vars:
            html_string = re.sub(r'\$slider\s+' + var + r'\$',
                                slider_div.format(element_class=self.html_class,
                                                  element_id=self.html_id,
                                                  var=var),
                                html_string, flags=re.IGNORECASE | re.UNICODE)

        # substitute numbers
        inputs = json.loads(self.configuration_json)['root']['inputs']['input']
        if type(inputs) == dict:
            inputs = [inputs]
        vars = [x['@var'] for x in inputs]

        input_div = '<span class="{element_class}_input" id="{element_id}_input_{var}" \
        data-var="{var}"></span>'

        for var in vars:
            html_string = re.sub(r'\$input\s+' + var + r'\$',
                                input_div.format(element_class=self.html_class,
                                                 element_id=self.html_id,
                                                 var=var),
                                html_string, flags=re.IGNORECASE | re.UNICODE)
        # import ipdb; ipdb.set_trace()
        return html_string

    def get_configuration(self):
        """Parse self.definition['configuration'] and transfer it to javascript
        via json.
        """
        # root added for interface compatibility with xmltodict.parse
        self.configuration_json = json.dumps(
                xmltodict.parse('<root>' +
                stringify_children(self.definition['configuration'])
                             + '</root>'))
        return self.configuration_json


class GraphicalSliderToolDescriptor(MakoModuleDescriptor, XmlDescriptor):
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
                raise ValueError("Self a\ssessment definition must include \
                    exactly one '{0}' tag".format(child))

        expected_children_level_1 = ['plot']
        for child in expected_children_level_1:
            if len(xml_object.xpath('configuration')[0].xpath(child)) != 1:
                raise ValueError("Self a\ssessment definition must include \
                    exactly one '{0}' tag".format(child))
        # finished

        def parse(k):
            """Assumes that xml_object has child k"""
            return stringify_children(xml_object.xpath(k)[0])

        return {
                    'render': parse('render'),
                    'configuration': xml_object.xpath('configuration')[0]
                }

    def definition_to_xml(self, resource_fs):
        '''Return an xml element representing this definition.
        Not implemented'''
        # import ipdb; ipdb.set_trace()
        xml_object = etree.Element('gst')

        def add_child(k):
            # child_str = '<{tag}>{body}</{tag}>'.format(tag=k, body=self.definition[k])
            child_str = child.export_to_xml(resource_fs)
            child_node = etree.fromstring(child_str)
            xml_object.append(child_node)

        for child in self.get_children():
            add_child(child)

        return xml_object
