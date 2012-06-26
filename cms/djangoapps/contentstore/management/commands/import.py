### 
### One-off script for importing courseware form XML format
###

from django.core.management.base import BaseCommand
from keystore.django import keystore
from raw_module import RawDescriptor
from lxml import etree
from fs.osfs import OSFS
from mako.lookup import TemplateLookup

from path import path
from x_module import XModuleDescriptor, XMLParsingSystem

unnamed_modules = 0

etree.set_default_parser(etree.XMLParser(dtd_validation=False, load_dtd=False,
                                         remove_comments=True))

class Command(BaseCommand):
    help = \
'''Import the specified data directory into the default keystore'''

    def handle(self, *args, **options):
        org, course, data_dir = args
        data_dir = path(data_dir)
        class ImportSystem(XMLParsingSystem):
            def __init__(self):
                self.load_item = keystore().get_item
                self.fs = OSFS(data_dir)

            def process_xml(self, xml):
                try:
                    xml_data = etree.fromstring(xml)
                except:
                    print xml
                    raise
                if not xml_data.get('name'):
                    global unnamed_modules
                    unnamed_modules += 1
                    xml_data.set('name', '{tag}_{count}'.format(tag=xml_data.tag, count=unnamed_modules))

                module = XModuleDescriptor.load_from_xml(etree.tostring(xml_data), self, org, course, RawDescriptor)
                keystore().create_item(module.url)
                if 'data' in module.definition:
                    keystore().update_item(module.url, module.definition['data'])
                if 'children' in module.definition:
                    keystore().update_children(module.url, module.definition['children'])
                return module

        lookup = TemplateLookup(directories=[data_dir])
        template = lookup.get_template("course.xml")
        course_string = template.render(groups=[])
        ImportSystem().process_xml(course_string)
