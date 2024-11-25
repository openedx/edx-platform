# lint-amnesty, pylint: disable=missing-module-docstring
import logging
import re

from lxml import etree
from xblock.fields import Scope, String

from .exceptions import SerializationError

log = logging.getLogger(__name__)

PRE_TAG_REGEX = re.compile(r'<pre\b[^>]*>(?:(?=([^<]+))\1|<(?!pre\b[^>]*>))*?</pre>')


class RawMixin:
    """
    Common code between RawDescriptor and XBlocks converted from XModules.
    """
    resources_dir = None

    data = String(help="XML data for the block", default="", scope=Scope.content)

    @classmethod
    def definition_from_xml(cls, xml_object, system):  # lint-amnesty, pylint: disable=missing-function-docstring, unused-argument
        return {'data': etree.tostring(xml_object, pretty_print=True, encoding='unicode')}, []

    def definition_to_xml(self, resource_fs):  # lint-amnesty, pylint: disable=unused-argument
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
                "Unable to create xml for block {loc}. "
                "Context: '{context}'"
            ).format(
                context=lines[line - 1][offset - 40:offset + 40],
                loc=self.location,
            )
            raise SerializationError(self.location, msg)  # lint-amnesty, pylint: disable=raise-missing-from

    @classmethod
    def parse_xml_new_runtime(cls, node, runtime, keys):
        """
        Interpret the parsed XML in `node`, creating a new instance of this
        module.
        """
<<<<<<< HEAD
        # In the new/blockstore-based runtime, XModule parsing (from
=======
        # In the new/learning-core-based runtime, XModule parsing (from
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        # XmlMixin) is disabled, so definition_from_xml will not be
        # called, and instead the "normal" XBlock parse_xml will be used.
        # However, it's not compatible with RawMixin, so we implement
        # support here.
        data_field_value = cls.definition_from_xml(node, None)[0]["data"]
        for child in node.getchildren():
            node.remove(child)
        # Get attributes, if any, via normal parse_xml.
        try:
            block = super().parse_xml_new_runtime(node, runtime, keys)
        except AttributeError:
            block = super().parse_xml(node, runtime, keys)
        block.data = data_field_value
        return block


class EmptyDataRawMixin:
    """
    Common code between EmptyDataRawDescriptor and XBlocks converted from XModules.
    """
    resources_dir = None

    data = String(default='', scope=Scope.content)

    @classmethod
    def definition_from_xml(cls, xml_object, system):  # lint-amnesty, pylint: disable=unused-argument
        if len(xml_object) == 0 and len(list(xml_object.items())) == 0:
            return {'data': ''}, []
        return {'data': etree.tostring(xml_object, pretty_print=True, encoding='unicode')}, []

    def definition_to_xml(self, resource_fs):  # lint-amnesty, pylint: disable=unused-argument
        if self.data:
            return etree.fromstring(self.data)
        return etree.Element(self.category)
