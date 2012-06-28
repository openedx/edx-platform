###
### One-off script for importing courseware form XML format
###

from django.core.management.base import BaseCommand, CommandError
from keystore.django import keystore
from lxml import etree
from keystore.xml import XMLModuleStore

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

        module_store = XMLModuleStore(org, course, data_dir, 'xmodule.raw_module.RawDescriptor')
        for module in module_store.modules.itervalues():
            keystore().create_item(module.url)
            if 'data' in module.definition:
                keystore().update_item(module.url, module.definition['data'])
            if 'children' in module.definition:
                keystore().update_children(module.url, module.definition['children'])
