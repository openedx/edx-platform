import os
import sys
import traceback

from fs.osfs import OSFS
from path import path
from lxml import etree

from django.core.management.base import BaseCommand

from courseware.courses import get_course_by_id


def export(course, export_dir):
    """Export the specified course to course_dir.  Creates dir if it doesn't exist.
    Overwrites files, does not clean out dir beforehand.
    """
    fs = OSFS(export_dir, create=True)
    if not fs.isdirempty('.'):
        print ('WARNING: Directory {dir} not-empty.'
               '  May clobber/confuse things'.format(dir=export_dir))

    try:
        xml = course.export_to_xml(fs)
        with fs.open('course.xml', mode='w') as f:
            f.write(xml)

        return True
    except:
        print 'Export failed!'
        traceback.print_exc()

    return False


class Command(BaseCommand):
    help = """Exports specified course as xml files, in canonical format.

Usage: export_xml course_id PATH-TO-OUTPUT-DIR 
"""
    def handle(self, *args, **options):
        n = len(args)
        if not n == 2:
            print Command.help
            return

        course_id = args[0]
        export_dir = args[1]

        # get course by id
        course = get_course_by_id(course_id)

        export(course, export_dir)
