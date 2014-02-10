"""
Script for dumping course dumping the course structure
"""
from django.core.management.base import BaseCommand, CommandError
from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.django import modulestore
from json import dumps
from xmodule.modulestore.inheritance import own_metadata
from django.conf import settings

filter_list = ['xml_attributes', 'checklists']


class Command(BaseCommand):
    """
    The Django command for dumping course structure
    """
    help = '''Write out to stdout a structural and metadata information about a course in a flat dictionary serialized
              in a JSON format. This can be used for analytics.'''

    def handle(self, *args, **options):
        "Execute the command"
        if len(args) < 1 or len(args) > 2:
            raise CommandError("dump_course_structure requires two or more arguments: <location> |<db>|")

        course_id = args[0]

        # use a user-specified database name, if present
        # this is useful for doing dumps from databases restored from prod backups
        if len(args) == 2:
            settings.MODULESTORE['direct']['DOC_STORE_CONFIG']['db'] = args[1]

        loc = CourseDescriptor.id_to_location(course_id)

        store = modulestore()

        course = store.get_item(loc, depth=4)

        info = {}

        def dump_into_dict(module, info):
            filtered_metadata = dict((key, value) for key, value in own_metadata(module).iteritems()
                                     if key not in filter_list)
            info[module.location.url()] = {
                'category': module.location.category,
                'children': module.children if hasattr(module, 'children') else [],
                'metadata': filtered_metadata
            }

            for child in module.get_children():
                dump_into_dict(child, info)

        outfile = '{0}.json'.format(loc.course)

        dump_into_dict(course, info)

        with open(outfile, 'w') as f:
            f.write(dumps(info))
