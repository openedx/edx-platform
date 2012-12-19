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
        resource_string(__name__, 'js/src/graphical_slider_tool/el_output.js'),

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
        plot_def = re.search(r'<plot[^<>]*/>', html_string)
        if plot_def:
            plot_def = plot_def.group()
            style = re.search(r'(?=.*style\=[\"\'](.*)[\"\'])', plot_def,
                flags=re.UNICODE | re.DOTALL)
            if style:
                style = style.groups()[0]
            else:  # no style parameter
                style = ''
            replacement = plot_div.format(element_class=self.html_class,
                                          element_id=self.html_id,
                                                style=style)
            html_string = re.sub(r'<plot[^<>]*/>', replacement, html_string,
                            flags=re.UNICODE)

        # get variables
        if json.loads(self.configuration_json)['root'].get('parameters'):
            variables = json.loads(self.configuration_json)['root']['parameters']['param']
            if type(variables) == dict:
                variables = [variables]
            variables = [x['@var'] for x in variables]
        else:
            return html_string
        # if variables[0] == 'v':
        #     import ipdb; ipdb.set_trace()
        #substitute sliders
        slider_div = '<div class="{element_class}_slider" \
                                   id="{element_id}_slider_{var}" \
                                   data-var="{var}" style="{style}">\
                     </div>'
        for var in variables:
            # find <slider var='var' ... >
            instances = re.findall(r'<slider\s+(?=[^<>]*var\=[\"\']' + var + '[\"\'])' \
                          + r'[^<>]*/>', html_string, flags=re.UNICODE | re.DOTALL)
            if instances:  # if presented, only one slider per var
                slider_def = instances[0]  # get <slider var='var' ... > string
                # extract var for proper style extraction further
                var_substring = re.search(r'(var\=[\"\']' + var + r'[\"\'])',
                                          slider_def).group()
                slider_def = slider_def.replace(var_substring, '')
                # get style
                style = re.search(r'(?=[^<>]*style\=[\"\'](.*)[\"\'])', slider_def,
                    flags=re.UNICODE | re.DOTALL)
                if style:
                    style = style.groups()[0]
                else:  # no style parameter
                    style = ''
                # substitute parameters to slider div
                replacement = slider_div.format(element_class=self.html_class,
                                            element_id=self.html_id,
                                            var=var, style=style)
                # subsitute <slider var='var' ... > in html_srting to proper
                # html div element
                html_string = re.sub(r'<slider\s+(?=[^<>]*var\=[\"\'](' + \
                    var + ')[\"\'])' + r'[^<>]*/>',
                replacement, html_string, flags=re.UNICODE | re.DOTALL)

        # substitute inputs if we have them
        input_el = '<input class="{element_class}_input" \
                                  id="{element_id}_input_{var}_{input_index}" \
                                   data-var="{var}" style="{style}" \
                                   data-el_readonly="{readonly}"/>'

        for var in variables:
            input_index = 0  # make multiple inputs for same variable have
                # different id
            instances = re.findall(r'<textbox\s+(?=[^<>]*var\=[\"\']' + var + '[\"\'])' \
                          + r'[^<>]*/>', html_string, flags=re.UNICODE | re.DOTALL)
            # import ipdb; ipdb.set_trace()
            for input_def in instances:  # for multiple inputs per var
                input_index += 1
                # extract var and readonly before style!
                # import ipdb; ipdb.set_trace()
                var_substring = re.search(r'(var\=[\"\']' + var + r'[\"\'])',
                                          input_def).group()
                input_def = input_def.replace(var_substring, '')
                readonly = re.search(r'(?=[^<>]*(readonly\=[\"\'](\w+)[\"\']))', 
                    input_def, flags=re.UNICODE | re.DOTALL)
                if readonly:
                    input_def = input_def.replace(readonly.groups()[0], '')
                    readonly = readonly.groups()[1]
                else:
                    readonly = ''
                style = re.search(r'(?=[^<>]*style\=[\"\'](.*)[\"\'])', input_def,
                    flags=re.UNICODE | re.DOTALL)
                if style:
                    style = style.groups()[0]
                else:
                    style = ''
                # import ipdb; ipdb.set_trace()
                replacement = input_el.format(element_class=self.html_class,
                        element_id=self.html_id,
                        var=var, readonly=readonly, style=style,
                        input_index=input_index)
                # import ipdb; ipdb.set_trace()
                html_string = re.sub(r'<textbox\s+(?=[^<>]*var\=[\"\'](' + \
                                     var + ')[\"\'])' + r'[^<>]*/>',
                replacement, html_string, count=1, flags=re.UNICODE | re.DOTALL)
        return html_string

    def get_configuration(self):
        """Parse self.definition['configuration'] and transfer it to javascript
        via json.
        """
        # root added for interface compatibility with xmltodict.parse
        # import ipdb; ipdb.set_trace()
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
