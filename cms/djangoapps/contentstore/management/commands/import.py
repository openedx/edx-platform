### 
### One-off script for importing courseware form XML format
###

from django.core.management.base import BaseCommand
from keystore.django import keystore
from raw_module import RawDescriptor
from lxml import etree

from path import path
from x_module import XModuleDescriptor, DescriptorSystem

unnamed_modules = 0

etree.set_default_parser(etree.XMLParser(dtd_validation=False, load_dtd=False,
                                         remove_comments=True))

class Command(BaseCommand):
    help = \
'''Import the specified data directory into the default keystore'''

    def handle(self, *args, **options):
        org, course, data_dir = args
        data_dir = path(data_dir)
        with open(data_dir / "course.xml") as course_file:

            system = DescriptorSystem(keystore().get_item)

            def process_xml(xml):
                try:
                    xml_data = etree.fromstring(xml)
                except:
                    print xml
                    raise
                if not xml_data.get('name'):
                    global unnamed_modules
                    unnamed_modules += 1
                    xml_data.set('name', 'Unnamed module %d' % unnamed_modules)


                module = XModuleDescriptor.load_from_xml(etree.tostring(xml_data), system, org, course, RawDescriptor)
                keystore().create_item(module.url)
                if 'data' in module.definition:
                    keystore().update_item(module.url, module.definition['data'])
                if 'children' in module.definition:
                    keystore().update_children(module.url, module.definition['children'])
                return module.url

            system.process_xml = process_xml
            system.process_xml(course_file.read())
