###
### One-off script for importing courseware form XML format
###

from django.core.management.base import BaseCommand, CommandError
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.xml import XMLModuleStore

unnamed_modules = 0


class Command(BaseCommand):
    help = \
'''Import the specified data directory into the default ModuleStore'''

    def handle(self, *args, **options):
        if len(args) != 3:
            raise CommandError("import requires 3 arguments: <org> <course> <data directory>")

        org, course, data_dir = args

        module_store = XMLModuleStore(org, course, data_dir, 'xmodule.raw_module.RawDescriptor', eager=True)
        for module in module_store.modules.itervalues():
            modulestore().create_item(module.location)
            if 'data' in module.definition:
                modulestore().update_item(module.location, module.definition['data'])
            if 'children' in module.definition:
                modulestore().update_children(module.location, module.definition['children'])
            modulestore().update_metadata(module.location, dict(module.metadata))
