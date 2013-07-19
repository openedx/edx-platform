from django.core.management.base import BaseCommand, CommandError
from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.django import modulestore
from json import dumps
from xmodule.modulestore.inheritance import own_metadata
from django.conf import settings

filter_list = ['xml_attributes', 'checklists']


class Command(BaseCommand):
    help = '''Write out to stdout a structural and metadata information about a course in a flat dictionary serialized
              in a JSON format. This can be used for analytics.'''

    def handle(self, *args, **options):
        if len(args) < 2 or len(args) > 3:
            raise CommandError("dump_course_structure requires two or more arguments: <location> <outfile> |<db>|")

        course_id = args[0]
        outfile = args[1]

        # use a user-specified database name, if present
        # this is useful for doing dumps from databases restored from prod backups
        if len(args) == 3:
            settings.MODULESTORE['direct']['OPTIONS']['db'] = args[2]

        loc = CourseDescriptor.id_to_location(course_id)

        store = modulestore()

        course = None
        try:
            course = store.get_item(loc, depth=4)
        except:
            print 'Could not find course at {0}'.format(course_id)
            return

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

        dump_into_dict(course, info)

        with open(outfile, 'w') as f:
            f.write(dumps(info))
