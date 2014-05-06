"""
Export all xml courses in a diffable format.

This command loads all of the xml courses in the configured DATA_DIR.
For each of the courses, it loops through all of the modules, and dumps
each as a separate output file containing the json representation
of each of its fields (including those fields that are set as default values).
"""

from __future__ import print_function

import json
from path import path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from xmodule.modulestore.xml import XMLModuleStore


class Command(BaseCommand):
    """
    Django management command to export diffable representations of all xml courses
    """
    help = '''Dump the in-memory representation of all xml courses in a diff-able format'''
    args = '<export path>'

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError('Must called with arguments: {}'.format(self.args))

        xml_module_store = XMLModuleStore(
            data_dir=settings.DATA_DIR,
            default_class='xmodule.hidden_module.HiddenDescriptor',
            load_error_modules=True,
            xblock_mixins=settings.XBLOCK_MIXINS,
            xblock_select=settings.XBLOCK_SELECT_FUNCTION,
        )

        export_dir = path(args[0])

        for course_id, course_modules in xml_module_store.modules.iteritems():
            course_path = course_id.replace('/', '_')
            for location, descriptor in course_modules.iteritems():
                location_path = location.to_deprecated_string().replace('/', '_')
                data = {}
                for field_name, field in descriptor.fields.iteritems():
                    try:
                        data[field_name] = field.read_json(descriptor)
                    except Exception as exc:  # pylint: disable=broad-except
                        data[field_name] = {
                            '$type': str(type(exc)),
                            '$value': descriptor._field_data.get(descriptor, field_name)  # pylint: disable=protected-access
                        }

                outdir = export_dir / course_path
                outdir.makedirs_p()
                with open(outdir / location_path + '.json', 'w') as outfile:
                    json.dump(data, outfile, sort_keys=True, indent=4)
                    print('', file=outfile)
