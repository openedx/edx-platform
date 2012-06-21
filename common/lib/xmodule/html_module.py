import json
import logging

from x_module import XModule
from mako_module import MakoModuleDescriptor
from lxml import etree

log = logging.getLogger("mitx.courseware")


#-----------------------------------------------------------------------------
class HtmlModuleDescriptor(MakoModuleDescriptor):
    """
    Module for putting raw html in a course
    """
    mako_template = "widgets/html-edit.html"

    # TODO (cpennington): Make this into a proper module
    js = {'coffee': ["""
        window.construct_html = (id) ->
            $('#' + id + " #edit-box").on('input', ->
                $('#' + id + ' #edit-preview').empty().append($(this).val())
            )
    """]}


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
