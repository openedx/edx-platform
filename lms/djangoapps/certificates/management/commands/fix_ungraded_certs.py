"""
Management command which fixes ungraded certificates for students
"""
import logging
import types

from django.core.management.base import BaseCommand
from opaque_keys.edx.keys import CourseKey

from certificates.models import GeneratedCertificate
from courseware import courses
from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to find and grade all students that need to be graded.
    """

    help = """
    Find all students that need to be graded
    and grade them.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-n',
            '--noop',
            action='store_true',
            dest='noop',
            default=False,
            help="Print but do not update the GeneratedCertificate table"
        )

        parser.add_argument(
            '-c',
            '--course',
            metavar='COURSE_ID',
            dest='course',
            required=True,
            help='Grade ungraded users for this course'
        )

    def handle(self, *args, **options):
        course_id = options['course']
        log.info('Fetching ungraded students for %s.', course_id)

        # I got an error in testing that course wasn't an OpaqueKey. Not sure if this is an old command
        # or if we're calling it programmatically with OpaqueKey types, but I attempted to handle it here.
        if isinstance(options['course'], types.StringType):
            course_key = CourseKey.from_string(options['course'])
        else:
            course_key = options['course']

        ungraded = GeneratedCertificate.objects.filter(  # pylint: disable=no-member
            course_id__exact=course_key
        ).filter(grade__exact='')
        course = courses.get_course_by_id(course_key)
        for cert in ungraded:
            # grade the student
            grade = CourseGradeFactory().read(cert.user, course)
            log.info('grading %s - %s', cert.user, grade.percent)
            cert.grade = grade.percent
            if not options['noop']:
                cert.save()
