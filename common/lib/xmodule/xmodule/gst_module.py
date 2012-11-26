"""
GST (Graphical-Slider-Tool) module is ungraded xmodule used by students to
understand functional dependencies
"""

# import json
import logging

from lxml import etree

from xmodule.mako_module import MakoModuleDescriptor
from xmodule.xml_module import XmlDescriptor
from xmodule.x_module import XModule
from xmodule.progress import Progress
from xmodule.exceptions import NotFoundError
from pkg_resources import resource_string
from xmodule.raw_module import RawDescriptor

# log = logging.getLogger("mitx.common.lib.seq_module")


class GSTModule(XModule):
    ''' Graphical-Slider-Tool Module
    '''
    # js = {'js': [resource_string(__name__, 'js/src/gst/gst.js')]}
    # #css = {'scss': [resource_string(__name__, 'css/capa/display.scss')]}
    # js_module_name = "GST"

    def __init__(self, system, location, definition, descriptor, instance_state=None,
                 shared_state=None, **kwargs):
        """
        pass
    #     Definition  should have....
    #     sliders, text, module

    #     Sample file:

    #     <gst>
    #         <h2> Plot... </h2>
    #         <slider name="1" var="a"/>
    #         <number name="1" var="a"/>
    #         <plot/>
    #         <sliders_info>
    #         <sliders/>
    #         <numbers_info>
    #         </numbers_info
    #         <plot_info>
    #         </plot_info>
    #     </gst>
    #     """
    #     XModule.__init__(self, system, location, definition, descriptor,
    #                      instance_state, shared_state, **kwargs)
    #     import ipdb; ipdb.set_trace()
    #     self.rendered = False

    # def get_html(self):
    #     self.render()
    #     return self.content

    # def render(self):
    #     import ipdb; ipdb.set_trace()
    #     if self.rendered:
    #         return
    #     ## Returns a set of all types of all sub-children
    #     contents = []
    #     # import ipdb; ipdb.set_trace()
    #     for child in self.get_display_items():
    #         progress = child.get_progress()
    #         childinfo = {
    #             'gst': child.get_html(),
    #             'plot': "\n".join(
    #                 grand_child.display_name.strip()
    #                 for grand_child in child.get_children()
    #                 if 'display_name' in grand_child.metadata
    #             ),
    #             # 'progress_status': Progress.to_js_status_str(progress),
    #             'progress_detail': Progress.to_js_detail_str(progress),
    #             'type': child.get_icon_class(),
    #         }
    #         # if childinfo['title']=='':
    #             # childinfo['title'] = child.metadata.get('display_name','')
    #         contents.append(childinfo)

    #     params = {'items': contents,
    #               'element_id': self.location.html_id(),
    #               'item_id': self.id,
    #               'position': self.position,
    #               'tag': self.location.category
    #               }

    #     self.content = self.system.render_template('seq_module.html', params)
    #     self.rendered = True


class GSTDescriptor(RawDescriptor):
    mako_template = "widgets/html-edit.html"
    module_class = GSTModule
    template_dir_name = 'gst'

    # @classmethod
    # def definition_from_xml(cls, xml_object, system):
    #     """
    #     Pull out the data into dictionary.

    #     Returns:
    #     {
    #     'def1': 'def1-some-html',
    #     'def2': 'def2-some-html'
    #     }
    #     """
    #     import ipdb; ipdb.set_trace()
    #     children = []
    #     for child in xml_object:
    #         try:
    #             children.append(system.process_xml(etree.tostring(child)).location.url())
    #         except:
    #             log.exception("Unable to load child when parsing GST. Continuing...")
    #             continue
    #     return {'children': children}

    # def definition_to_xml(self, resource_fs):
    #     '''Return an xml element representing this definition.'''
    #     import ipdb; ipdb.set_trace()
    #     xml_object = etree.Element('gst')

    #     def add_child(k):
    #         # child_str = '<{tag}>{body}</{tag}>'.format(tag=k, body=self.definition[k])
    #         child_str = child.export_to_xml(resource_fs)
    #         child_node = etree.fromstring(child_str)
    #         xml_object.append(child_node)

    #     for child in self.get_children():
    #         add_child(child)

    #     return xml_object


    # def __init__(self, system, definition, **kwargs):
    #     '''Render and save the template for this descriptor instance'''
    #     super(CustomTagDescriptor, self).__init__(system, definition, **kwargs)
    #     self.rendered_html = self.render_template(system, definition['data'])