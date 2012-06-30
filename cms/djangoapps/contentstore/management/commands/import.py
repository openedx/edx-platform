###
### One-off script for importing courseware form XML format
###

from django.core.management.base import BaseCommand, CommandError
from keystore.django import keystore
from keystore.xml import XMLModuleStore

unnamed_modules = 0


class Command(BaseCommand):
    help = \
'''Import the specified data directory into the default keystore'''

    def handle(self, *args, **options):
        if len(args) != 3:
            raise CommandError("import requires 3 arguments: <org> <course> <data directory>")

        org, course, data_dir = args

        module_store = XMLModuleStore(org, course, data_dir, 'xmodule.raw_module.RawDescriptor', eager=True)
        for module in module_store.modules.itervalues():
            keystore().create_item(module.location)
            if 'data' in module.definition:
                keystore().update_item(module.location, module.definition['data'])
            if 'children' in module.definition:
                keystore().update_children(module.location, module.definition['children'])
            keystore().update_metadata(module.location, dict(module.metadata))
