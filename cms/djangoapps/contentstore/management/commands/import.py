###
### One-off script for importing courseware form XML format
###

from django.core.management.base import BaseCommand, CommandError
from keystore.django import keystore
from raw_module import RawDescriptor
from lxml import etree
from fs.osfs import OSFS

from path import path
from x_module import XModuleDescriptor, XMLParsingSystem

unnamed_modules = 0

etree.set_default_parser(etree.XMLParser(dtd_validation=False, load_dtd=False,
                                         remove_comments=True))


class Command(BaseCommand):
    help = \
'''Import the specified data directory into the default keystore'''

    def handle(self, *args, **options):
        if len(args) != 3:
            raise CommandError("import requires 3 arguments: <org> <course> <data directory>")

        org, course, data_dir = args
        data_dir = path(data_dir)
        with open(data_dir / "course.xml") as course_file:

            class ImportSystem(XMLParsingSystem):
                def __init__(self):
                    def process_xml(xml):
                        try:
                            xml_data = etree.fromstring(xml)
                        except:
                            raise CommandError("Unable to parse xml: " + xml)

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

                    XMLParsingSystem.__init__(self, keystore().get_item, OSFS(data_dir), process_xml)

            ImportSystem().process_xml(course_file.read())
