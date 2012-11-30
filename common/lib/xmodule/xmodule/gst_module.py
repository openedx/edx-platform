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


log = logging.getLogger("mitx.common.lib.gst_module")


class GraphicalSliderToolModule(XModule):
    ''' Graphical-Slider-Tool Module
    '''
    # js = {'js': [resource_string(__name__, 'js/src/gst/gst.js')]}
    # #css = {'scss': [resource_string(__name__, 'css/capa/display.scss')]}
    # js_module_name = "GST"

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
                Graphic slider tool html. Can include
                'number', 'slider' and plot tags. They will be replaced
                by proper number, slider and plot widgets.
              </render>
              <configuration>
                <sliders>
                  <slider name="1" var="a" range="-100, 1, 100" />
                </sliders>
                <numbers>
                  <number name="1" var="a"/>
                </numbers>
                <plot>
                  <function name="1" y="x^2 + a"/>
                  <function name="2" y="3*x + b"/>
                  <!-- xrange and yrange are optional -->
                  <xrange>-10, 1, 10</xrange>
                  <!-- xticks and yticks are optional -->
                  <xticks>1</xticks>
                  <yticks>1</yticks>
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
        gst_html = self.substitute_controls(self.definition['render'].strip())

        params = {
                  'gst_html': gst_html,
                  'element_id': self.location.html_id(),
                  'element_class': self.location.category,
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
        plot_div = '<div class="${element_class}_plot" id="${element_id}_plot" \
        style="width: 600px; height: 600px; padding: 0px; position: relative;"> \
        This is plot</div>'
        html_string.replace('$plot$', plot_div)
        vars = [x['@var'] for x in json.loads(self.configuration_json)['root']['sliders']['slider']]
        for var in vars:
            m = re.match('$slider\[([0-9]+),([0-9]+)]', self.value.strip().replace(' ', ''))
        if m:
            # Note: we subtract 15 to compensate for the size of the dot on the screen.
            # (is a 30x30 image--lms/static/green-pointer.png).
            (self.gx, self.gy) = [int(x) - 15 for x in m.groups()]
        html.replace('$slider' + ' ' + x['@var'])
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
                    'configuration': xml_object.xpath('configuration')[0],
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
