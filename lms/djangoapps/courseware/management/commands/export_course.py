"""
A Django command that exports a course to a tar.gz file.

If <filename> is '-', it pipes the file to stdout

"""

import os
import re
import shutil
import tarfile
from tempfile import mktemp, mkdtemp
from textwrap import dedent

from path import Path as path

from django.core.management.base import BaseCommand, CommandError

from xmodule.modulestore.django import modulestore
from xmodule.modulestore.xml_exporter import export_course_to_xml
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey


class Command(BaseCommand):
    """
    Export a course to XML. The output is compressed as a tar.gz file

    """
    args = "<course_id> <output_filename>"
    help = dedent(__doc__).strip()

    def handle(self, *args, **options):
        course_key, filename, pipe_results = self._parse_arguments(args)

        export_course_to_tarfile(course_key, filename)

        results = self._get_results(filename) if pipe_results else None

        self.stdout.write(results, ending="")

    def _parse_arguments(self, args):
        """Parse command line arguments"""
        try:
            course_key = CourseKey.from_string(args[0])
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

        return course_key, filename, pipe_results

    def _get_results(self, filename):
        """Load results from file"""
        with open(filename) as f:
            results = f.read()
            os.remove(filename)
        return results


def export_course_to_tarfile(course_key, filename):
    """Exports a course into a tar.gz file"""
    tmp_dir = mkdtemp()
    try:
        course_dir = export_course_to_directory(course_key, tmp_dir)
        compress_directory(course_dir, filename)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def export_course_to_directory(course_key, root_dir):
    """Export course into a directory"""
    store = modulestore()
    course = store.get_course(course_key)
    if course is None:
        raise CommandError("Invalid course_id")

    # The safest characters are A-Z, a-z, 0-9, <underscore>, <period> and <hyphen>.
    # We represent the first four with \w.
    # TODO: Once we support courses with unicode characters, we will need to revisit this.
    replacement_char = u'-'
    course_dir = replacement_char.join([course.id.org, course.id.course, course.id.run])
    course_dir = re.sub(r'[^\w\.\-]', replacement_char, course_dir)

    export_course_to_xml(store, None, course.id, root_dir, course_dir)

    export_dir = path(root_dir) / course_dir
    return export_dir


def compress_directory(directory, filename):
    """Compress a directory into a tar.gz file"""
    mode = 'w:gz'
    name = path(directory).name
    with tarfile.open(filename, mode) as tar_file:
        tar_file.add(directory, arcname=name)
