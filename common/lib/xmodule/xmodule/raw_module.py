from pkg_resources import resource_string
from lxml import etree
from xmodule.mako_module import MakoModuleDescriptor
from xmodule.xml_module import XmlDescriptor


class RawDescriptor(MakoModuleDescriptor, XmlDescriptor):
    """
    Module that provides a raw editing view of it's data and children
    """
    mako_template = "widgets/raw-edit.html"

    js = {'coffee': [resource_string(__name__, 'js/module/raw.coffee')]}
    js_module = 'Raw'

    def get_context(self):
        return {
            'module': self,
            'data': self.definition['data'],
        }

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        return {'data': etree.tostring(xml_object)}

    def definition_to_xml(self, resource_fs):
        return etree.fromstring(self.definition['data'])
