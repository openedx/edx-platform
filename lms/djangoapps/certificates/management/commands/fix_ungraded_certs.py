"""
Management command which fixes ungraded certificates for students
"""
from django.core.management.base import BaseCommand
import logging
from optparse import make_option

from certificates.models import GeneratedCertificate
from courseware import courses
from lms.djangoapps.grades.new.course_grade import CourseGradeFactory


log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to find and grade all students that need to be graded.
    """

    help = """
    Find all students that need to be graded
    and grade them.
    """

    option_list = BaseCommand.option_list + (
        make_option(
            '-n',
            '--noop',
            action='store_true',
            dest='noop',
            default=False,
            help="Print but do not update the GeneratedCertificate table"
        ),
        make_option(
            '-c',
            '--course',
            metavar='COURSE_ID',
            dest='course',
            default=False,
            help='Grade ungraded users for this course'
        ),
    )

    def handle(self, *args, **options):
        course_id = options['course']
        log.info('Fetching ungraded students for %s.', course_id)
        ungraded = GeneratedCertificate.objects.filter(  # pylint: disable=no-member
            course_id__exact=course_id
        ).filter(grade__exact='')
        course = courses.get_course_by_id(course_id)
        for cert in ungraded:
            # grade the student
            grade = CourseGradeFactory().create(cert.user, course)
            log.info('grading %s - %s', cert.user, grade.percent)
            cert.grade = grade.percent
            if not options['noop']:
                cert.save()
