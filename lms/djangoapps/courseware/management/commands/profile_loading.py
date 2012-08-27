"""
A script for profiling xml import.  Just imports the specified class.
"""

import cProfile
from pstats import Stats
import os
import sys
import traceback

from filecmp import dircmp
from fs.osfs import OSFS
from path import path
from lxml import etree

from django.core.management.base import BaseCommand

from xmodule.modulestore.xml import XMLModuleStore
from xmodule.errortracker import make_error_tracker

def traverse_tree(course):
    '''Load every descriptor in course.  Return bool success value.'''

    url_names = set()
    bad = False

    queue = [course]
    while len(queue) > 0:
        node = queue.pop()
        if node.url_name in url_names:
            print "WARNING: {0} repeats, {1}.".format(node.url_name, node.location.url())
            bad = True
        url_names.add(node.url_name)
        queue.extend(node.get_children())

    return not bad


def import_with_checks(course_dir, verbose=True):
    all_ok = True

    print "Attempting to load '{0}'".format(course_dir)

    course_dir = path(course_dir)
    data_dir = course_dir.dirname()
    course_dirs = [course_dir.basename()]

    # No default class--want to complain if it doesn't find plugins for any
    # module.
    modulestore = XMLModuleStore(data_dir,
                   default_class=None,
                   eager=True,
                   course_dirs=course_dirs)

    def str_of_err(tpl):
        (msg, exc_str) = tpl
        return '{msg}\n{exc}'.format(msg=msg, exc=exc_str)

    courses = modulestore.get_courses()

    n = len(courses)
    if n != 1:
        print 'ERROR: Expect exactly 1 course.  Loaded {n}: {lst}'.format(
            n=n, lst=courses)
        return (False, None)

    course = courses[0]
    errors = modulestore.get_item_errors(course.location)
    if len(errors) != 0:
        all_ok = False
        print '\n'
        print "=" * 40
        print 'ERRORs during import:'
        print '\n'.join(map(str_of_err, errors))
        print "=" * 40
        print '\n'


    #print course
    validators = (
        traverse_tree,
        )

    print "=" * 40
    print "Running validators..."

    for validate in validators:
        print 'Running {0}'.format(validate.__name__)
        all_ok = validate(course) and all_ok


    if all_ok:
        print 'Course passes all checks!'
    else:
        print "Course fails some checks.  See above for errors."
    return all_ok, course


def profile(course_dir):
    cProfile.runctx('import_with_checks(course_dir)', globals(), locals(), 'import.prof')
    s = Stats('import.prof')
    s.sort_stats("cum").print_stats(50)


class Command(BaseCommand):
    help = """Imports specified course.xml, validate it, then exports in
    a canonical format.

Usage: profile_loading PATH-TO-COURSE-DIR

"""
    def handle(self, *args, **options):
        n = len(args)
        if n < 1 or n > 1:
            print Command.help
            return
        profile(args[0])
