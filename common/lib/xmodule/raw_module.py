from pkg_resources import resource_string
from mako_module import MakoModuleDescriptor
from lxml import etree

class RawDescriptor(MakoModuleDescriptor):
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
            definition={'data': xml_data},
            location=['i4x',
                      org,
                      course,
                      xml_object.tag,
                      xml_object.get('name')]
        )
