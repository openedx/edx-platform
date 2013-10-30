"""
A Django command that dumps the structure of a course as a JSON object.

The resulting JSON object has one entry for each module in the course:

{
  "$module_url": {
    "category": "$module_category",
    "children": [$module_children_urls... ],
    "metadata": {$module_metadata}
  },

  "$module_url": ....
  ...
}

"""

import json
from optparse import make_option
from textwrap import dedent

from django.core.management.base import BaseCommand, CommandError

from xmodule.modulestore.django import modulestore
from xmodule.modulestore.inheritance import own_metadata


FILTER_LIST = ['xml_attributes', 'checklists']


class Command(BaseCommand):
    """
    Write out to stdout a structural and metadata information for a
    course as a JSON object
    """
    args = "<course_id>"
    help = dedent(__doc__).strip()
    option_list = BaseCommand.option_list + (
        make_option('--modulestore',
                    action='store',
                    default='default',
                    help='Name of the modulestore'),
    )

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("course_id not specified")

        # Get the modulestore

        try:
            name = options['modulestore']
            store = modulestore(name)
        except KeyError:
            raise CommandError("Unknown modulestore {}".format(name))

        # Get the course data

        course_id = args[0]
        course = store.get_course(course_id)
        if course is None:
            raise CommandError("Invalid course_id")

        # Convert course data to dictionary and dump it as JSON to stdout

        info = dump_module(course)

        return json.dumps(info, indent=2, sort_keys=True)


def dump_module(module, destination=None):
    """
    Add the module and all its children to the destination dictionary in
    as a flat structure.
    """

    destination = destination if destination else {}

    items = own_metadata(module).iteritems()
    filtered_metadata = {k: v for k, v in items if k not in FILTER_LIST}

    destination[module.location.url()] = {
        'category': module.location.category,
        'children': module.children if hasattr(module, 'children') else [],
        'metadata': filtered_metadata
    }

    for child in module.get_children():
        dump_module(child, destination)

    return destination
