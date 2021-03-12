import logging
import re

from lxml import etree
from xblock.fields import Scope, String
from xmodule.editing_module import XMLEditingDescriptor
from xmodule.xml_module import XmlDescriptor

from .exceptions import SerializationError

log = logging.getLogger(__name__)

PRE_TAG_REGEX = re.compile(r'<pre\b[^>]*>(?:(?=([^<]+))\1|<(?!pre\b[^>]*>))*?</pre>')


class RawMixin(object):
    """
    Common code between RawDescriptor and XBlocks converted from XModules.
    """
    resources_dir = None

    data = String(help="XML data for the module", default="", scope=Scope.content)

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        try:
            data = etree.tostring(xml_object, pretty_print=True, encoding='unicode')
            pre_tag_data = []
            for pre_tag_info in xml_object.findall('.//pre'):
                if len(pre_tag_info.findall('.//pre')) == 0:
                    pre_tag_data.append(etree.tostring(pre_tag_info))

            if pre_tag_data:
                matches = re.finditer(PRE_TAG_REGEX, data)
                for match_num, match in enumerate(matches):
                    data = re.sub(match.group(), pre_tag_data[match_num].decode(), data)
            etree.XML(data)  # it just checks if generated string is valid xml
            return {'data': data}, []
        except etree.XMLSyntaxError:
            return {'data': etree.tostring(xml_object, pretty_print=True, encoding='unicode')}, []

    def definition_to_xml(self, resource_fs):
        """
        Return an Element if we've kept the import OLX, or None otherwise.
        """
        # If there's no self.data, it means that an XBlock/XModule originally
        # existed for this data at the time of import/editing, but was later
        # uninstalled. RawDescriptor therefore never got to preserve the
        # original OLX that came in, and we have no idea how it should be
        # serialized for export. It's possible that we could do some smarter
        # fallback here and attempt to extract the data, but it's reasonable
        # and simpler to just skip this node altogether.
        if not self.data:
            log.warning(
                "Could not serialize %s: No XBlock installed for '%s' tag.",
                self.location,
                self.location.block_type,
            )
            return None

        # Normal case: Just echo back the original OLX we saved.
        try:
            return etree.fromstring(self.data)
        except etree.XMLSyntaxError as err:
            # Can't recover here, so just add some info and
            # re-raise
            lines = self.data.split('\n')
            line, offset = err.position
            msg = (
                u"Unable to create xml for module {loc}. "
                u"Context: '{context}'"
            ).format(
                context=lines[line - 1][offset - 40:offset + 40],
                loc=self.location,
            )
            raise SerializationError(self.location, msg)

    @classmethod
    def parse_xml_new_runtime(cls, node, runtime, keys):
        """
        Interpret the parsed XML in `node`, creating a new instance of this
        module.
        """
        # In the new/blockstore-based runtime, XModule parsing (from
        # XmlMixin) is disabled, so definition_from_xml will not be
        # called, and instead the "normal" XBlock parse_xml will be used.
        # However, it's not compatible with RawMixin, so we implement
        # support here.
        data_field_value = cls.definition_from_xml(node, None)[0]["data"]
        for child in node.getchildren():
            node.remove(child)
        # Get attributes, if any, via normal parse_xml.
        try:
            block = super(RawMixin, cls).parse_xml_new_runtime(node, runtime, keys)
        except AttributeError:
            block = super(RawMixin, cls).parse_xml(node, runtime, keys, id_generator=None)
        block.data = data_field_value
        return block


class RawDescriptor(RawMixin, XmlDescriptor, XMLEditingDescriptor):
    """
    Module that provides a raw editing view of its data and children.  It
    requires that the definition xml is valid.
    """
    pass


class EmptyDataRawMixin(object):
    """
    Common code between EmptyDataRawDescriptor and XBlocks converted from XModules.
    """
    resources_dir = None

    data = String(default='', scope=Scope.content)

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        if len(xml_object) == 0 and len(list(xml_object.items())) == 0:
            return {'data': ''}, []
        return {'data': etree.tostring(xml_object, pretty_print=True, encoding='unicode')}, []

    def definition_to_xml(self, resource_fs):
        if self.data:
            return etree.fromstring(self.data)
        return etree.Element(self.category)


class EmptyDataRawDescriptor(EmptyDataRawMixin, XmlDescriptor, XMLEditingDescriptor):
    """
    Version of RawDescriptor for modules which may have no XML data,
    but use XMLEditingDescriptor for import/export handling.
    """
    pass
