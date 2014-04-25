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
from xmodule.modulestore.inheritance import own_metadata, compute_inherited_metadata
from xblock.fields import Scope
from opaque_keys import InvalidKeyError
from xmodule.modulestore.locations import SlashSeparatedCourseKey

FILTER_LIST = ['xml_attributes', 'checklists']
INHERITED_FILTER_LIST = ['children', 'xml_attributes', 'checklists']


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
        make_option('--inherited',
                    action='store_true',
                    default=False,
                    help='Whether to include inherited metadata'),
        make_option('--inherited_defaults',
                    action='store_true',
                    default=False,
                    help='Whether to include default values of inherited metadata'),
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

        try:
            course_id = SlashSeparatedCourseKey.from_deprecated_string(args[0])
        except InvalidKeyError:
            raise CommandError("Invalid course_id")

        course = store.get_course(course_id)
        if course is None:
            raise CommandError("Invalid course_id")

        # precompute inherited metadata at the course level, if needed:
        if options['inherited']:
            compute_inherited_metadata(course)

        # Convert course data to dictionary and dump it as JSON to stdout

        info = dump_module(course, inherited=options['inherited'], defaults=options['inherited_defaults'])

        return json.dumps(info, indent=2, sort_keys=True)


def dump_module(module, destination=None, inherited=False, defaults=False):
    """
    Add the module and all its children to the destination dictionary in
    as a flat structure.
    """

    destination = destination if destination else {}

    items = own_metadata(module)
    filtered_metadata = {k: v for k, v in items.iteritems() if k not in FILTER_LIST}

    destination[module.location.to_deprecated_string()] = {
        'category': module.location.category,
        'children': [child.to_deprecated_string() for child in getattr(module, 'children', [])],
        'metadata': filtered_metadata,
    }

    if inherited:
        # when calculating inherited metadata, don't include existing
        # locally-defined metadata
        inherited_metadata_filter_list = list(filtered_metadata.keys())
        inherited_metadata_filter_list.extend(INHERITED_FILTER_LIST)

        def is_inherited(field):
            if field.name in inherited_metadata_filter_list:
                return False
            elif field.scope != Scope.settings:
                return False
            elif defaults:
                return True
            else:
                return field.values != field.default

        inherited_metadata = {field.name: field.read_json(module) for field in module.fields.values() if is_inherited(field)}
        destination[module.location.to_deprecated_string()]['inherited_metadata'] = inherited_metadata

    for child in module.get_children():
        dump_module(child, destination, inherited, defaults)

    return destination
