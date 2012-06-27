from xmodule.x_module import XModuleDescriptor
from lxml import etree


class XmlDescriptor(XModuleDescriptor):
    """
    Mixin class for standardized parsing of from xml
    """

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        """
        Return the definition to be passed to the newly created descriptor
        during from_xml
        """
        raise NotImplementedError("%s does not implement definition_from_xml" % cls.__class__.__name__)

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
            cls.definition_from_xml(xml_object, system),
            location=['i4x',
                      org,
                      course,
                      xml_object.tag,
                      xml_object.get('slug')],
            display_name=xml_object.get('name')
        )
