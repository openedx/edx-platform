"""
Xml parsing tests for XModules
"""
import pprint
from mock import Mock

from xmodule.x_module import XMLParsingSystem
from xmodule.mako_module import MakoDescriptorSystem
from xmodule.modulestore.xml import create_block_from_xml


class InMemorySystem(XMLParsingSystem, MakoDescriptorSystem):  # pylint: disable=abstract-method
    """
    The simplest possible XMLParsingSystem
    """
    def __init__(self, xml_import_data):
        self.org = xml_import_data.org
        self.course = xml_import_data.course
        self.default_class = xml_import_data.default_class
        self._descriptors = {}
        super(InMemorySystem, self).__init__(
            policy=xml_import_data.policy,
            process_xml=self.process_xml,
            load_item=self.load_item,
            error_tracker=Mock(),
            resources_fs=xml_import_data.filesystem,
            mixins=xml_import_data.xblock_mixins,
            render_template=lambda template, context: pprint.pformat((template, context))
        )

    def process_xml(self, xml):  # pylint: disable=method-hidden
        """Parse `xml` as an XBlock, and add it to `self._descriptors`"""
        descriptor = create_block_from_xml(xml, self, self.org, self.course, self.default_class)
        self._descriptors[descriptor.location.url()] = descriptor
        return descriptor

    def load_item(self, location):  # pylint: disable=method-hidden
        """Return the descriptor loaded for `location`"""
        return self._descriptors[location]


class XModuleXmlImportTest(object):
    """Base class for tests that use basic XML parsing"""
    def process_xml(self, xml_import_data):
        """Use the `xml_import_data` to import an :class:`XBlock` from XML."""
        system = InMemorySystem(xml_import_data)
        return system.process_xml(xml_import_data.xml_string)
