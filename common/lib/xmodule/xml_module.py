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
        raise NotImplementedError("%s does not implement definition_from_xml" % cls.__name__)

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

        metadata = {}
        for attr in ('format', 'graceperiod', 'showanswer', 'rerandomize', 'due'):
            from_xml = xml_object.get(attr)
            if from_xml is not None:
                metadata[attr] = from_xml

        if xml_object.get('graded') is not None:
            metadata['graded'] = xml_object.get('graded') == 'true'

        if xml_object.get('name') is not None:
            metadata['display_name'] = xml_object.get('name')

        return cls(
            system,
            cls.definition_from_xml(xml_object, system),
            location=['i4x',
                      org,
                      course,
                      xml_object.tag,
                      xml_object.get('slug')],
            metadata=metadata,
        )

    def export_to_xml(self, resource_fs):
        """
        Returns an xml string representing this module, and all modules underneath it.
        May also write required resources out to resource_fs

        Assumes that modules have single parantage (that no module appears twice in the same course),
        and that it is thus safe to nest modules as xml children as appropriate.

        The returned XML should be able to be parsed back into an identical XModuleDescriptor
        using the from_xml method with the same system, org, and course
        """
        xml_object = self.definition_to_xml(resource_fs)
        xml_object.set('slug', self.name)
        xml_object.tag = self.type

        for attr in ('format', 'graceperiod', 'showanswer', 'rerandomize', 'due'):
            if attr in self.metadata:
                xml_object.set(attr, self.metadata[attr])

        if 'graded' in self.metadata:
            xml_object.set('graded', str(self.metadata['graded']).lower())

        if 'display_name' in self.metadata:
            xml_object.set('name', self.metadata['display_name'])

        return etree.tostring(xml_object, pretty_print=True)

    def definition_to_xml(self, resource_fs):
        """
        Return a new etree Element object created from this modules definition.
        """
        raise NotImplementedError("%s does not implement definition_to_xml" % self.__class__.__name__)
