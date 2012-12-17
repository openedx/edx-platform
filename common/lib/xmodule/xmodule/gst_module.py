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
        For XML file format please look at documentation.

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
        plot_div = '<div class="{element_class}_plot" id="{element_id}_plot" \
                    style="{style}"></div>'
        # extract css style from plot
        plot_def = re.search(r'\$\s*plot[^\$]*\$', html_string).group()
        style = re.search(r'(?=.*style\=[\"\'](.*)[\"\'])', plot_def)
        if style:
            style = style.groups()[0]
        else:  # no style parameter
            style = ''
        replacement = plot_div.format(element_class=self.html_class,
                                      element_id=self.html_id,
                                            style=style)
        html_string = re.sub(r'\$\s*plot[^\$]*\$', replacement, html_string,
                        flags=re.IGNORECASE | re.UNICODE)

        # get variables
        if json.loads(self.configuration_json)['root'].get('parameters'):
            variables = json.loads(self.configuration_json)['root']['parameters']['param']
            if type(variables) == dict:
                variables = [variables]
            variables = [x['@var'] for x in variables]
        else:
            return html_string

        #substitute sliders
        slider_div = '<div class="{element_class}_slider" \
                                   id="{element_id}_slider_{var}" \
                                   data-var="{var}" data-el_style="{style}">\
                     </div>'
        for var in variables:
            # find $slider var='var' ... $
            instances = re.findall(r'\$\s*slider\s+(?=.*var\=[\"\']' + var + '[\"\'])' \
                          + r'[^\$]*\$', html_string)
            if instances:  # if presented, only one slider per var
                slider_def = instances[0]  # get $slider var='var' ... $ string
                # extract var for proper style extraction further
                var_substring = re.search(r'(var\=[\"\']' + var + r'[\"\'])',
                                          slider_def).group()
                slider_def = slider_def.replace(var_substring, '')
                # get style
                style = re.search(r'(?=.*style\=[\"\'](.*)[\"\'])', slider_def)
                if style:
                    style = style.groups()[0]
                else:  # no style parameter
                    style = ''
                # substitute parameters to slider div
                replacement = slider_div.format(element_class=self.html_class,
                                            element_id=self.html_id,
                                            var=var, style=style)
                # subsitute $slider var='var' ... $ in html_srting to proper
                # html div element
                html_string = re.sub(r'\$\s*slider\s+(?=.*var\=[\"\'](' + \
                    var + ')[\"\'])' + r'[^\$]*\$',
                replacement, html_string, flags=re.IGNORECASE | re.UNICODE)

        # substitute inputs if we have them
        input_el = '<input class="{element_class}_input" \
                                  id="{element_id}_input_{var}" \
                                   data-var="{var}" data-el_style="{style}" \
                                   data-el_readonly="{readonly}"/>'

        input_index = 0  # make multiple inputs for same variable have
        # different id

        for var in variables:
            input_index = +1
            instances = re.findall(r'\$\s*input\s+(?=.*var\=[\"\']' + var + '[\"\'])' \
                          + r'[^\$]*\$', html_string)
            # import ipdb; ipdb.set_trace()
            for input_def in instances:  # for multiple inputs per var
                # extract var and readonly before style!
                var_substring = re.search(r'(var\=[\"\']' + var + r'[\"\'])',
                                          input_def).group()
                input_def = input_def.replace(var_substring, '')
                readonly = re.search(r'(?=.*(readonly\=[\"\'](\w+)[\"\']))', input_def)
                if readonly:
                    input_def = input_def.replace(readonly.groups()[0], '')
                    readonly = readonly.groups()[1]
                else:
                    readonly = ''
                style = re.search(r'(?=.*style\=[\"\'](.*)[\"\'])', input_def)
                if style:
                    style = style.groups()[0]
                else:
                    style = ''

                replacement = input_el.format(element_class=self.html_class,
                        element_id=self.html_id + '_' + str(input_index),
                        var=var, readonly=readonly, style=style)
                # import ipdb; ipdb.set_trace()
                html_string = re.sub(r'\$\s*input\s+(?=.*var\=[\"\'](' + \
                                     var + ')[\"\'])' + r'[^\$]*\$',
                replacement, html_string, count=1, flags=re.IGNORECASE | re.UNICODE)
        return html_string

    def get_configuration(self):
        """Parse self.definition['configuration'] and transfer it to javascript
        via json.
        """
        # root added for interface compatibility with xmltodict.parse
        self.configuration_json = json.dumps(
                xmltodict.parse('<root class="' + self.location.category + '">' +
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
