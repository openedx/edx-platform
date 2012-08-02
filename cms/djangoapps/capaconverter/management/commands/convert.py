###
### One-off script for importing courseware form XML format
###

from django.core.management.base import BaseCommand, CommandError
import json
from capaconverter import CapaXMLConverter


class Command(BaseCommand):
    help = \
'''Import the specified data directory into the default ModuleStore'''

    def handle(self, *args, **options):
        self.converter = CapaXMLConverter()
        # print json.dumps(self.converter.convert_xml_file("/Users/ccp/code/mitx_all/mitx/1.xml"), indent=2)
        print json.dumps(self.converter.convert_xml_file("/Users/ccp/code/mitx_all/data/6.002x/problems/HW3ID1.xml"), indent=2)
        # print json.dumps(self.converter.convert_xml_file("/Users/ccp/code/mitx_all/data/6.002x/problems/multichoice.xml"), indent=2)
