"""
A Django command that exports a course to a tar.gz file.

If <filename> is '-', it pipes the file to stdout

"""

import os
import shutil
import tarfile
from tempfile import mktemp, mkdtemp
from textwrap import dedent

from path import path

from django.core.management.base import BaseCommand, CommandError

from xmodule.modulestore.django import modulestore
from xmodule.modulestore.xml_exporter import export_to_xml
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locations import SlashSeparatedCourseKey


class Command(BaseCommand):
    """
    Export a course to XML. The output is compressed as a tar.gz file

    """
    args = "<course_id> <output_filename>"
    help = dedent(__doc__).strip()

    def handle(self, *args, **options):
        course_id, filename, pipe_results = self._parse_arguments(args)

        export_course_to_tarfile(course_id, filename)

        results = self._get_results(filename) if pipe_results else None

        return results

    def _parse_arguments(self, args):
        """Parse command line arguments"""
        try:
            course_id = SlashSeparatedCourseKey.from_deprecated_string(args[0])
            filename = args[1]
        except InvalidKeyError:
            raise CommandError("Unparsable course_id")
        except IndexError:
            raise CommandError("Insufficient arguments")

        # If filename is '-' save to a temp file
        pipe_results = False
        if filename == '-':
            filename = mktemp()
            pipe_results = True

        return course_id, filename, pipe_results

    def _get_results(self, filename):
        """Load results from file"""
        with open(filename) as f:
            results = f.read()
            os.remove(filename)
        return results


def export_course_to_tarfile(course_id, filename):
    """Exports a course into a tar.gz file"""
    tmp_dir = mkdtemp()
    try:
        course_dir = export_course_to_directory(course_id, tmp_dir)
        compress_directory(course_dir, filename)
    finally:
        shutil.rmtree(tmp_dir)


def export_course_to_directory(course_id, root_dir):
    """Export course into a directory"""
    store = modulestore()
    course = store.get_course(course_id)
    if course is None:
        raise CommandError("Invalid course_id")

    course_name = course.id.to_deprecated_string().replace('/', '-')
    export_to_xml(store, None, course.id, root_dir, course_name)

    course_dir = path(root_dir) / course_name
    return course_dir


def compress_directory(directory, filename):
    """Compress a directrory into a tar.gz file"""
    mode = 'w:gz'
    name = path(directory).name
    with tarfile.open(filename, mode) as tar_file:
        tar_file.add(directory, arcname=name)
