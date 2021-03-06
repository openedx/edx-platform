"""
These modules exist to translate old format XML into newer, semantic forms
"""
from lxml import etree

from openedx.core.djangolib.markup import Text

from .x_module import XModuleDescriptor


class TranslateCustomTagDescriptor(XModuleDescriptor):  # lint-amnesty, pylint: disable=abstract-method, missing-class-docstring
    resources_dir = None

    @classmethod
    def from_xml(cls, xml_data, system, id_generator):
        """
        Transforms the xml_data from <$custom_tag attr="" attr=""/> to
        <customtag attr="" attr="" impl="$custom_tag"/>
        """

        xml_object = etree.fromstring(xml_data)
        system.error_tracker(Text('WARNING: the <{tag}> tag is deprecated.  '
                             'Instead, use <customtag impl="{tag}" attr1="..." attr2="..."/>. ')
                             .format(tag=xml_object.tag))

        tag = xml_object.tag
        xml_object.tag = 'customtag'
        xml_object.attrib['impl'] = tag

        return system.process_xml(etree.tostring(xml_object))
