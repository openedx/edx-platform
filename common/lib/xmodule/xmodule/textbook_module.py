from xmodule.x_module import XModule
from xmodule.xml_module import XmlDescriptor
from lxml import etree

class TextbookModule(XModule):
    def __init__(self, system, location, definition, descriptor, instance_state=None,
                 shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, descriptor,
                         instance_state, shared_state, **kwargs)

    def get_display_items(self):
      return []

class TextbookDescriptor(XmlDescriptor):

    module_class = TextbookModule

    def __init__(self, system, definition=None, **kwargs):
        super(TextbookDescriptor, self).__init__(system, definition, **kwargs)
        self.title = self.metadata["title"]

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        return { 'children': [] }

    @property
    def table_of_contents(self):
        raw_table_of_contents = open(self.metadata['table_of_contents_url'], 'r') # TODO: This will need to come from S3
        table_of_contents = etree.parse(raw_table_of_contents).getroot()
        return table_of_contents
