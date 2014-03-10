"""
A script to walk a course xml tree, generate a dictionary of all the metadata,
and print it out as a json dict.
"""
import sys
import json

from collections import OrderedDict
from path import path

from django.core.management.base import BaseCommand

from xmodule.modulestore.xml import XMLModuleStore
from xmodule.x_module import policy_key


def import_course(course_dir, verbose=True):
    course_dir = path(course_dir)
    data_dir = course_dir.dirname()
    course_dirs = [course_dir.basename()]

    # No default class--want to complain if it doesn't find plugins for any
    # module.
    modulestore = XMLModuleStore(data_dir,
                   default_class=None,
                   course_dirs=course_dirs)

    def str_of_err(tpl):
        (msg, exc_str) = tpl
        return '{msg}\n{exc}'.format(msg=msg, exc=exc_str)

    courses = modulestore.get_courses()

    n = len(courses)
    if n != 1:
        sys.stderr.write('ERROR: Expect exactly 1 course.  Loaded {n}: {lst}\n'.format(
            n=n, lst=courses))
        return None

    course = courses[0]
    errors = modulestore.get_course_errors(course.id)
    if len(errors) != 0:
        sys.stderr.write('ERRORs during import: {0}\n'.format('\n'.join(map(str_of_err, errors))))

    return course


def node_metadata(node):
    # make a copy
    to_export = ('format', 'display_name',
                 'graceperiod', 'showanswer', 'rerandomize',
                 'start', 'due', 'graded', 'hide_from_toc',
                 'ispublic', 'xqa_key')

    orig = own_metadata(node)
    d = {k: orig[k] for k in to_export if k in orig}
    return d


def get_metadata(course):
    d = OrderedDict({})
    queue = [course]
    while len(queue) > 0:
        node = queue.pop()
        d[policy_key(node.location)] = node_metadata(node)
        # want to print first children first, so put them at the end
        # (we're popping from the end)
        queue.extend(reversed(node.get_children()))
    return d


def print_metadata(course_dir, output):
    course = import_course(course_dir)
    if course:
        meta = get_metadata(course)
        result = json.dumps(meta, indent=4)
        if output:
            with file(output, 'w') as f:
                f.write(result)
        else:
            print result


class Command(BaseCommand):
    help = """Imports specified course.xml and prints its
metadata as a json dict.

Usage: metadata_to_json PATH-TO-COURSE-DIR OUTPUT-PATH

if OUTPUT-PATH isn't given, print to stdout.
"""
    def handle(self, *args, **options):
        n = len(args)
        if n < 1 or n > 2:
            print Command.help
            return

        output_path = args[1] if n > 1 else None
        print_metadata(args[0], output_path)
