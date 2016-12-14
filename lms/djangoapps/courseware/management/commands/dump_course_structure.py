"""
A Django command that dumps the structure of a course as a JSON object or CSV list.

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
import csv
import StringIO
from optparse import make_option
from textwrap import dedent

from django.core.management.base import BaseCommand, CommandError

from xmodule.modulestore.django import modulestore
from xmodule.modulestore.inheritance import own_metadata, compute_inherited_metadata
from xblock.fields import Scope
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

FILTER_LIST = ['xml_attributes']
INHERITED_FILTER_LIST = ['children', 'xml_attributes']


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
        make_option('--flat',
                    action='store_true',
                    dest='flat',
                    default=False,
                    help='Show "flattened" course content with order and levels'),
        make_option('--csv',
                    action='store_true',
                    dest='csv',
                    default=False,
                    help='output in CSV format (default is JSON)'),
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

        store = modulestore()

        # Get the course data

        try:
            course_key = CourseKey.from_string(args[0])
        except InvalidKeyError:
            raise CommandError("Invalid course_id")

        course = store.get_course(course_key)
        if course is None:
            raise CommandError("Invalid course_id")

        # Precompute inherited metadata at the course level, if needed:

        if options['inherited']:
            compute_inherited_metadata(course)

        # Convert course data to dictionary and dump it as JSON to stdout
        if options['flat']:
            info = dump_module_by_position(course_id, course)
        else:
            info = dump_module(course, inherited=options['inherited'], defaults=options['inherited_defaults'])

        if options['csv']:
            csvout = StringIO.StringIO()
            writer = csv.writer(csvout, dialect='excel')
            writer.writerows(info)
            return csvout.getvalue()

        return json.dumps(info, indent=2, sort_keys=True, default=unicode)


def dump_module(module, destination=None, inherited=False, defaults=False):
    """
    Add the module and all its children to the destination dictionary in
    as a flat structure.
    """

    destination = destination if destination else {}

    items = own_metadata(module)

    filtered_metadata = {k: v for k, v in items.iteritems() if k not in FILTER_LIST}

    destination[unicode(module.location)] = {
        'category': module.location.category,
        'children': [unicode(child) for child in getattr(module, 'children', [])],
        'metadata': filtered_metadata,
    }

    if inherited:
        # When calculating inherited metadata, don't include existing
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
        destination[unicode(module.location)]['inherited_metadata'] = inherited_metadata

    for child in module.get_children():
        dump_module(child, destination, inherited, defaults)

    return destination


def dump_module_by_position(course_id, module, level=0,
                            destination=None, prefix=None, parent=None):
    """
    Add a module and all of its children to the end of the list.
    Keep a running tally of position in the list and indent level.
    """
    pos = 0
    if destination:
        pos = destination[-1][1] + 1  # pos is the 2nd col

    if level == 0:
        display_name_long = ""
    elif level == 1:
        display_name_long = module.display_name
    else:
        display_name_long = prefix + "," + module.display_name

    if destination is None:
        destination = [
            (
                'course_id',
                'position',
                'level',
                'module_id',
                'type',
                'displayname',
                'path',
                'parent',
            ),
        ]

    destination.append(
        (
            course_id,
            pos,
            level,
            module.id,
            module.location.category,
            module.display_name,
            display_name_long,
            parent,
        )
    )
    for child in module.get_children():
        dump_module_by_position(
            course_id,
            child,
            level=level + 1,
            destination=destination,
            prefix=display_name_long,
            parent=module.id,
        )
    return destination
