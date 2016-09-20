"""
These modules exist to translate old format XML into newer, semantic forms
"""
from .x_module import XModuleDescriptor
from lxml import etree
from functools import wraps
import logging
import traceback

log = logging.getLogger(__name__)


def process_includes(fn):
    """
    Wraps a XModuleDescriptor.from_xml method, and modifies xml_data to replace
    any immediate child <include> items with the contents of the file that they
    are supposed to include
    """
    @wraps(fn)
    def from_xml(cls, xml_data, system, id_generator):
        xml_object = etree.fromstring(xml_data)
        next_include = xml_object.find('include')
        while next_include is not None:
            system.error_tracker("WARNING: the <include> tag is deprecated, and will go away.")
            file = next_include.get('file')
            parent = next_include.getparent()

            if file is None:
                continue

            try:
                ifp = system.resources_fs.open(file)
                # read in and convert to XML
                incxml = etree.XML(ifp.read())

                # insert  new XML into tree in place of include
                parent.insert(parent.index(next_include), incxml)
            except Exception:
                # Log error
                msg = "Error in problem xml include: %s" % (
                    etree.tostring(next_include, pretty_print=True))
                # tell the tracker
                system.error_tracker(msg)

                # work around
                parent = next_include.getparent()
                errorxml = etree.Element('error')
                messagexml = etree.SubElement(errorxml, 'message')
                messagexml.text = msg
                stackxml = etree.SubElement(errorxml, 'stacktrace')
                stackxml.text = traceback.format_exc()
                # insert error XML in place of include
                parent.insert(parent.index(next_include), errorxml)

            parent.remove(next_include)

            next_include = xml_object.find('include')
        return fn(cls, etree.tostring(xml_object), system, id_generator)
    return from_xml


class SemanticSectionDescriptor(XModuleDescriptor):
    resources_dir = None

    @classmethod
    @process_includes
    def from_xml(cls, xml_data, system, id_generator):
        """
        Removes sections with single child elements in favor of just embedding
        the child element
        """
        xml_object = etree.fromstring(xml_data)
        system.error_tracker("WARNING: the <{0}> tag is deprecated.  Please do not use in new content."
                             .format(xml_object.tag))

        if len(xml_object) == 1:
            for (key, val) in xml_object.items():
                xml_object[0].set(key, val)

            return system.process_xml(etree.tostring(xml_object[0]))
        else:
            xml_object.tag = 'sequential'
            return system.process_xml(etree.tostring(xml_object))


class TranslateCustomTagDescriptor(XModuleDescriptor):
    resources_dir = None

    @classmethod
    def from_xml(cls, xml_data, system, id_generator):
        """
        Transforms the xml_data from <$custom_tag attr="" attr=""/> to
        <customtag attr="" attr="" impl="$custom_tag"/>
        """

        xml_object = etree.fromstring(xml_data)
        system.error_tracker('WARNING: the <{tag}> tag is deprecated.  '
                             'Instead, use <customtag impl="{tag}" attr1="..." attr2="..."/>. '
                             .format(tag=xml_object.tag))

        tag = xml_object.tag
        xml_object.tag = 'customtag'
        xml_object.attrib['impl'] = tag

        return system.process_xml(etree.tostring(xml_object))
