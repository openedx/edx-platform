import json
import logging

from x_module import XModule
from mako_module import MakoModuleDescriptor
from lxml import etree
from pkg_resources import resource_string

log = logging.getLogger("mitx.courseware")


#-----------------------------------------------------------------------------
class HtmlModuleDescriptor(MakoModuleDescriptor):
    """
    Module for putting raw html in a course
    """
    mako_template = "widgets/html-edit.html"

    js = {'coffee': [resource_string(__name__, 'js/module/html.coffee')]}
    js_module = 'HTML'

    @classmethod
    def from_xml(cls, xml_data, system, org=None, course=None):
        """
        Creates an instance of this descriptor from the supplied xml_data.
        This may be overridden by subclasses

        xml_data: A string of xml that will be translated into data and children for
            this module
        system: An XModuleSystem for interacting with external resources
        org and course are optional strings that will be used in the generated modules
            url identifiers
        """
        xml_object = etree.fromstring(xml_data)
        return cls(
            system,
            definition={'data': {'text': xml_data}},
            location=['i4x',
                      org,
                      course,
                      xml_object.tag,
                      xml_object.get('name')]
        )

class Module(XModule):
    id_attribute = 'filename'

    def get_state(self):
        return json.dumps({ })

    @classmethod
    def get_xml_tags(c):
        return ["html"]
        
    def get_html(self):
        if self.filename==None:
            xmltree=etree.fromstring(self.xml)
            textlist=[xmltree.text]+[etree.tostring(i) for i in xmltree]+[xmltree.tail]
            textlist=[i for i in textlist if type(i)==str]
            return "".join(textlist)
        try: 
            filename="html/"+self.filename
            return self.filestore.open(filename).read()
        except: # For backwards compatibility. TODO: Remove
            if self.DEBUG:
                log.info('[courseware.modules.html_module] filename=%s' % self.filename)
            return self.system.render_template(self.filename, {'id': self.item_id}, namespace='course')

    def __init__(self, system, xml, item_id, state=None):
        XModule.__init__(self, system, xml, item_id, state)
        xmltree=etree.fromstring(xml)
        self.filename = None
        filename_l=xmltree.xpath("/html/@filename")
        if len(filename_l)>0:
            self.filename=str(filename_l[0])
